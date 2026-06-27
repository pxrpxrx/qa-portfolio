package com.tradingtabs.engine;

import java.util.*;

public class DivergenceScanner {
    private final DataManager.Snapshot data;

    public DivergenceScanner(DataManager.Snapshot data) {
        this.data = data;
    }

    public record Divergence(String label, String description, boolean bearish) {}

    public List<Divergence> scan() {
        List<Divergence> result = new ArrayList<>();

        double dxyTrend = DataManager.pctChange(data.dxyHistory(), 5);
        double btcMom = DataManager.pctChange(data.btcHistory(), 5);
        double hygSpread = Double.isNaN(data.baa10y()) ? 0 : data.baa10y();

        if (dxyTrend > 0.005 && btcMom > 0.02) {
            result.add(new Divergence("DXY up + BTC up",
                "Dollar strengthens, BTC rallies — fragile risk-on", true));
        }
        if (dxyTrend < -0.005 && btcMom > 0.02) {
            result.add(new Divergence("DXY down + BTC up",
                "Dollar weakens, BTC rallies — classic risk-on", false));
        }
        if (dxyTrend > 0.005 && btcMom < -0.02) {
            result.add(new Divergence("DXY up + BTC down",
                "Dollar strengthens, BTC falls — risk-off flight", true));
        }
        if (hygSpread > 5 && btcMom > 0.02) {
            result.add(new Divergence("HYG spread up + BTC up",
                "Credit spreads widen, BTC rallies — divergence", true));
        }
        if (hygSpread > 5 && btcMom < -0.02) {
            result.add(new Divergence("HYG spread up + BTC down",
                "Credit stress + BTC falling — confirmed risk-off", true));
        }
        if (!data.btcHistory().isEmpty()) {
            double m2MoM = DataManager.pctChange(data.m2History(), 1);
            double btcPct = DataManager.pctChange(data.btcHistory(), 5);
            if (m2MoM > 0.002 && btcPct < -0.02) {
                result.add(new Divergence("M2 up, BTC down",
                    "Liquidity expands but BTC falls — potential reversal up", false));
            }
            if (m2MoM < -0.002 && btcPct > 0.02) {
                result.add(new Divergence("M2 down, BTC up",
                    "Liquidity contracts but BTC rallies — fragile", true));
            }
        }

        return result;
    }
}
