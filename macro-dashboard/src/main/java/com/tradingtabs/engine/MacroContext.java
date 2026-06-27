package com.tradingtabs.engine;

import java.time.LocalDate;
import java.util.*;

public class MacroContext {
    private final DataManager.Snapshot data;

    public MacroContext(DataManager.Snapshot data) {
        this.data = data;
    }

    public record MacroResult(String status, double m2Momentum, double netLiquidity,
                              double hygSpread, double dxyTrend, double termSpread,
                              String explanation) {}

    public MacroResult assess() {
        double m2MoM = DataManager.pctChange(data.m2History(), 1);
        double netLiq = data.m2() - data.tga() - data.onrrp();
        double hygSpread = Double.isNaN(data.baa10y()) ? 0 : data.baa10y();
        double dxyTrend = DataManager.pctChange(data.dxyHistory(), 5);
        double term = Double.isNaN(data.dgs10()) || Double.isNaN(data.dgs3mo()) ? 0
            : data.dgs10() - data.dgs3mo();

        int green = 0, red = 0;

        if (m2MoM > 0.002) green++; else if (m2MoM < -0.002) red++;
        if (term > 0) green++; else if (term < -0.5) red++;
        if (dxyTrend < -0.005) green++; else if (dxyTrend > 0.005) red++;
        if (hygSpread < 4.5) green++; else if (hygSpread > 6.0) red++;

        String status;
        if (green >= 3) status = "GREEN";
        else if (red >= 2) status = "RED";
        else status = "YELLOW";

        String expl = explain(status, m2MoM, term, dxyTrend, hygSpread, netLiq);
        return new MacroResult(status, m2MoM, netLiq, hygSpread, dxyTrend, term, expl);
    }

    private String explain(String status, double m2, double term, double dxy,
                           double hygSpread, double netLiq) {
        List<String> parts = new ArrayList<>();
        if (m2 > 0.002) parts.add("M2 up +" + String.format("%.1f", m2*100) + "%");
        else if (m2 < -0.002) parts.add("M2 down " + String.format("%.1f", m2*100) + "%");
        if (term > 0) parts.add("curve normal");
        else if (term < -0.5) parts.add("curve inverted " + String.format("%.1f", term) + "pp");
        if (dxy < -0.005) parts.add("DXY weak");
        else if (dxy > 0.005) parts.add("DXY strong");
        if (hygSpread < 3) parts.add("HYG " + String.format("%.1f", hygSpread) + "% risk-on");
        else if (hygSpread > 6) parts.add("HYG " + String.format("%.1f", hygSpread) + "% stress");
        return String.join(", ", parts);
    }
}
