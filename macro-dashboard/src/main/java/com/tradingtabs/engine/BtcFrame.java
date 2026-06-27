package com.tradingtabs.engine;

import java.util.*;

public class BtcFrame {
    private static final double BTC_DAILY_VOL = 0.035;

    private final DataManager.Snapshot data;

    public BtcFrame(DataManager.Snapshot data) {
        this.data = data;
    }

    public record BtcResult(String status, double support1, double support2,
                            double resistance1, double resistance2, double fairValue,
                            double fundingZ, double momentum, String explanation) {}

    public BtcResult assess() {
        double price = data.btcPrice();
        if (Double.isNaN(price) || price <= 0) {
            return new BtcResult("YELLOW", 0, 0, 0, 0, 0, 0, 0, "no BTC price data");
        }

        List<Double> hist = data.btcHistory();
        double ma = hist.isEmpty() ? price : DataManager.mean(hist);
        double fair = ma;
        double momentum = DataManager.pctChange(hist, hist.size() > 5 ? 5 : 1);
        double fr = data.btcFunding();
        double fundingZ = (fr > 0.0001) ? 1.0 : (fr < -0.0001) ? -1.0 : 0.0;

        double vol = BTC_DAILY_VOL;
        double support1 = fair * (1 - vol);
        double support2 = fair * (1 - 2 * vol);
        double resistance1 = fair * (1 + vol);
        double resistance2 = fair * (1 + 2 * vol);

        int green = 0, red = 0;

        if (price > fair) green++; else if (price < fair * 0.9) red++;
        if (fundingZ > -1 && fundingZ < 1) green++;
        else if (fundingZ < -2 || fundingZ > 2) red++;
        if (momentum > 0.02) green++; else if (momentum < -0.02) red++;
        if (data.btcVolume() > 0 && !Double.isNaN(data.btcOi())) {
            double volOi = data.btcVolume() / data.btcOi();
            if (!Double.isNaN(volOi) && volOi > 0.05) green++;
        }

        String status;
        if (green >= 3) status = "GREEN";
        else if (red >= 2) status = "RED";
        else status = "YELLOW";

        String expl = explain(status, price, fair, fundingZ, momentum);
        return new BtcResult(status, support1, support2, resistance1, resistance2,
            fair, fundingZ, momentum, expl);
    }

    private String explain(String status, double price, double fair,
                           double fundingZ, double momentum) {
        List<String> parts = new ArrayList<>();
        double pct = (price / fair - 1) * 100;
        parts.add(String.format("%+.1f%% from MA", pct));
        parts.add("funding Z=" + String.format("%.1f", fundingZ));
        return String.join(", ", parts);
    }
}
