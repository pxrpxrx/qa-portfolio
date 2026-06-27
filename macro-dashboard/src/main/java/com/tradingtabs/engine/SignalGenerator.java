package com.tradingtabs.engine;

import java.util.*;

public class SignalGenerator {
    private final MacroContext.MacroResult macro;
    private final BtcFrame.BtcResult btc;
    private final List<DivergenceScanner.Divergence> divergences;

    public SignalGenerator(MacroContext.MacroResult macro, BtcFrame.BtcResult btc,
                           List<DivergenceScanner.Divergence> divergences) {
        this.macro = macro;
        this.btc = btc;
        this.divergences = divergences;
    }

    public record Signal(String direction, String strength, String confluence,
                         double confidence, double allocation, double invalidation,
                         String reasoning) {}

    public Signal generate() {
        if (macro == null && btc == null)
            return new Signal("HOLD", "FLAT", "—", 0, 0, 0, "нет данных");

        int mScore = macroScore();
        int bScore = btcScore();
        int dScore = divScore();

        // Confluence: status-based, not score-threshold based
        int confluence = 0;
        String confLabel;
        String mStatus = macro != null ? macro.status() : null;
        String bStatus = btc != null ? btc.status() : null;
        if (mStatus != null && mStatus.equals(bStatus)) {
            confluence = 2;       confLabel = "CONFLUENCE";
        } else if (mStatus != null && bStatus != null
            && (("GREEN".equals(mStatus) && "RED".equals(bStatus))
             || ("RED".equals(mStatus) && "GREEN".equals(bStatus)))) {
            confluence = 0;       confLabel = "CONFLICT";
        } else {
            confluence = 1;       confLabel = "PARTIAL";
        }

        int raw = mScore + bScore + dScore + confluence;
        int maxM = macro != null ? 5 : 0;
        int maxB = btc != null ? 5 : 0;
        int max = maxM + maxB + 2 + 2; // base + divergences + confluence
        double ratio = max > 0 ? (double) raw / max : 0.5;

        // Direction & strength — CONFLICT override: only divergences can tip
        String dir, strength;
        if (confLabel.equals("CONFLICT") && Math.abs(dScore) <= 1) {
            dir = "HOLD";       strength = "FLAT";
        } else if (ratio >= 0.7) { dir = "LONG"; strength = ratio >= 0.85 ? "STRONG" : "MODERATE"; }
        else if (ratio >= 0.45) { dir = "LONG"; strength = "CAUTIOUS"; }
        else if (ratio <= 0.25) { dir = "SHORT"; strength = ratio <= 0.15 ? "STRONG" : "MODERATE"; }
        else if (ratio <= 0.4) { dir = "SHORT"; strength = "CAUTIOUS"; }
        else { dir = "HOLD"; strength = "FLAT"; }

        // Confidence: strength + confluence based
        double confidence;
        if (dir.equals("HOLD")) {
            confidence = 0;
        } else {
            double strengthBase = switch (strength) {
                case "STRONG" -> 0.85;
                case "MODERATE" -> 0.65;
                default -> 0.50; // CAUTIOUS
            };
            double confMult = switch (confLabel) {
                case "CONFLUENCE" -> 1.0;
                case "PARTIAL" -> 0.90;
                default -> 0.70; // CONFLICT (if divergences broke through)
            };
            confidence = Math.min(0.95, Math.max(0.05, strengthBase * confMult));
        }

        // Allocation: progressive, not jumpy
        double alloc;
        if (dir.equals("HOLD")) alloc = 0;
        else if (confidence >= 0.8) alloc = 0.75;
        else if (confidence >= 0.65) alloc = 0.50;
        else if (confidence >= 0.5) alloc = 0.25;
        else alloc = 0.10;

        // Invalidation: where the trade is wrong
        double invalidation = calcInvalidation(dir);

        String reasoning = buildReason(dir, mScore, bScore, dScore, confluence, confLabel);
        return new Signal(dir, strength, confLabel, confidence, alloc, invalidation, reasoning);
    }

    private int macroScore() {
        if (macro == null) return 0;
        return switch (macro.status()) {
            case "GREEN" -> 5;
            case "YELLOW" -> 2;
            default -> 0;
        };
    }

    private int btcScore() {
        if (btc == null) return 0;
        return switch (btc.status()) {
            case "GREEN" -> 5;
            case "YELLOW" -> 2;
            default -> 0;
        };
    }

    private int divScore() {
        if (divergences == null || divergences.isEmpty()) return 0;
        int bearish = 0;
        for (var d : divergences)
            if (d.bearish()) bearish++;
        int nonBearish = divergences.size() - bearish;
        int net = nonBearish - bearish;
        return Math.max(-2, Math.min(2, net));
    }

    private double calcInvalidation(String dir) {
        if (btc == null) return 0;
        return dir.equals("LONG") ? btc.support2() * 0.95
             : dir.equals("SHORT") ? btc.resistance2() * 1.05
             : 0;
    }

    private String buildReason(String dir, int m, int b, int d, int c, String cl) {
        List<String> p = new ArrayList<>();
        if (macro != null) p.add("macro=" + macro.status() + "(" + m + ")");
        if (btc != null) p.add("btc=" + btc.status() + "(" + b + ")");
        p.add("div=" + d);
        p.add(cl + "(" + c + ")");
        if (btc != null && btc.status().equals("RED")) p.add("⚠ BTC ниже MA");
        if (btc != null && btc.momentum() < -0.02) p.add("⚠ BTC momentum -" + String.format("%.0f", Math.abs(btc.momentum())*100) + "%");
        if (dir.equals("LONG") && btc != null && btc.support2() > 0)
            p.add("inv=" + String.format("%.0f", calcInvalidation(dir)));
        return String.join(" | ", p);
    }
}
