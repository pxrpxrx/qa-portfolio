package com.tradingtabs.gann;

import com.tradingtabs.horizon.HorizonMatrix.MetricRow;
import java.util.*;

public class AutoAnalyzer {

    private static final String DASH = "\u2500".repeat(46);

    public record Signal(String theme, String text, boolean isBullish) {}

    public record Analysis(String verdictLabel, List<Signal> signals, String summary) {}

    public static Analysis analyze(List<MetricRow> rows) {
        Map<String,MetricRow> byPair = new HashMap<>();
        Map<String,MetricRow> byLabel = new HashMap<>();
        for (MetricRow r : rows) {
            byPair.put(r.pair(), r);
            byLabel.put(r.label(), r);
        }

        List<Signal> signals = new ArrayList<>();
        boolean hasXli = byPair.containsKey("XLK/XLI");

        // TECH THEME
        check(byPair.get("NVDA/XLK"), signals, "Technology",
            "market leader (NVDA) growing faster than sector (XLK) \u2014 all good",
            v -> v < 1.0, "leader (NVDA) lags sector (XLK) \u2014 driver fading",
            d -> d < 0, "leader losing impulse \u2014 NVDA weakening vs tech sector");

        check(byPair.get("XLK/XLU"), signals, "Technology",
            "tech sector (XLK) stronger than defensive stocks (XLU) \u2014 investors trust growth",
            v -> v < 3.0, "defensives (XLU) beat tech (XLK) \u2014 flight from risk",
            d -> d < 0, "investors rotating from tech into defensives");

        check(byPair.get("QQQ/TLT"), signals, "Technology",
            "tech (QQQ) more expensive than bonds (TLT) \u2014 market in risk-on",
            v -> v < 6.0, "bonds (TLT) catching up to tech (QQQ) \u2014 fear, flight to safety",
            d -> d < 0, "investors fleeing tech into bonds");

        if (hasXli) {
            check(byPair.get("XLK/XLI"), signals, "Technology",
                "money flowing into tech (XLK) \u2014 innovation prioritized",
                v -> v < 0.6, "money leaving tech for industrials (XLI) \u2014 rotation",
                d -> d < 0, "flows reversing from tech into industrials");
        }

        // MARKET MOOD THEME
        check(byPair.get("QQQ/VIX"), signals, "Market Mood",
            "volatility low \u2014 market calm",
            v -> v < 25, "volatility high \u2014 panic",
            d -> d < 0, "volatility rising \u2014 market nervous");

        check(byPair.get("SPX/TLT"), signals, "Market Mood",
            "investors prefer stocks (SPX) over bonds (TLT) \u2014 greed",
            v -> v < 6, "investors fleeing stocks to bonds \u2014 fear",
            d -> d < 0, "fear rising \u2014 investors moving to bonds");

        check(byPair.get("DXY/XLF"), signals, "Market Mood",
            "dollar stronger than financials (XLF) \u2014 tight but tolerable",
            v -> v < 2.0, "dollar weaker than financials \u2014 cheap money",
            d -> d > 0, "dollar strengthening \u2014 liquidity tightening");

        check(byPair.get("DXY/TLT"), signals, "Market Mood",
            "dollar more expensive than bonds (TLT) \u2014 tight conditions",
            v -> v < 1.2, "bonds beating dollar \u2014 easing",
            d -> d > 0, "financial conditions tightening");

        // CONSUMER THEME
        check(byPair.get("XLY/XLP"), signals, "Consumer",
            "people spend on 'wants' (XLY) \u2014 economy strong",
            v -> v < 1.05, "people save, buy only necessities (XLP) \u2014 recession",
            d -> d < 0, "consumer confidence falling \u2014 people economizing");

        if (hasXli) {
            check(byPair.get("NG/XLI"), signals, "Economy",
                "energy demand rising \u2014 economy gaining momentum",
                v -> v < 0.02, "energy demand falling \u2014 economy slowing",
                d -> d > 0, "energy demand recovering");
        }

        check(byPair.get("HG1/XAU"), signals, "Economy",
            "copper (HG1) rising faster than gold (XAU) \u2014 expansion",
            v -> v < 0.08, "gold beating copper \u2014 fear of downturn",
            d -> d < 0, "economic fears growing");

        check(byPair.get("TLT/NG"), signals, "Economy",
            "bonds (TLT) more expensive than energy (NG) \u2014 market expects slowdown",
            v -> v < 20, "energy more expensive than bonds \u2014 inflationary growth",
            d -> d > 0, "market expects slowdown");

        // CREDIT THEME
        MetricRow bp = byLabel.get("BOILING POINT");
        if (bp != null) {
            String note = bp.note(); String cur = bp.current(); String prior = bp.prior();
            boolean isDown = "DOWN".equals(bp.dir());
            note = (note == null) ? "" : note;
            if (note.contains("credit stress"))
                signals.add(new Signal("Credit", "HYG low (" + cur + "): credit market in stress", false));
            else if (note.contains("credit strong"))
                signals.add(new Signal("Credit", "HYG high (" + cur + "): credit market strong", true));
            else
                signals.add(new Signal("Credit", "HYG " + cur + ": credit market normal (above 75) \u2014 no stress", true));
            if (isDown) signals.add(new Signal("Credit", "HYG falling (" + cur + " vs " + prior + ") \u2014 credit worsening", false));
        }

        MetricRow bt = byLabel.get("BANK TUNNEL");
        if (bt != null) {
            String note = bt.note(); String cur = bt.current(); String prior = bt.prior();
            boolean isDown = "DOWN".equals(bt.dir());
            note = (note == null) ? "" : note;
            if (note.contains("lending tight"))
                signals.add(new Signal("Credit", "SRLN low (" + cur + "): banks tightening lending", false));
            else if (note.contains("lending healthy"))
                signals.add(new Signal("Credit", "SRLN " + cur + ": banks lending actively", true));
            else
                signals.add(new Signal("Credit", "SRLN " + cur + ": lending at lower boundary of normal", true));
            if (isDown) signals.add(new Signal("Credit", "SRLN falling (" + cur + " vs " + prior + ") \u2014 banks cautious", false));
        }

        check(byPair.get("TLT/SHY"), signals, "Credit",
            "yield curve steep \u2014 economy normal",
            v -> v < 1.05, "yield curve flattening \u2014 recession signal",
            d -> d < 0, "yield curve falling \u2014 market expects slowdown");

        MetricRow cc = byLabel.get("CREDIT CYCLE");
        if (cc != null) {
            double val = parseDouble(cc.current());
            if (val < 1.5)
                signals.add(new Signal("Credit", "BAA10Y " + val + " \u2014 EUPHORIA. Credit cheap \u2014 cycle peak", true));
            else if (val < 2.5)
                signals.add(new Signal("Credit", "BAA10Y " + val + " \u2014 NORMAL. Credit market stable", true));
            else if (val < 4.0)
                signals.add(new Signal("Credit", "BAA10Y " + val + " \u2014 STRESS. Credit stress", false));
            else
                signals.add(new Signal("Credit", "BAA10Y " + val + " \u2014 PANIC. Credit crisis", false));
        }

        // ASSET FLOWS THEME
        check(byPair.get("XAU/TLT"), signals, "Capital Flows",
            "gold (XAU) more expensive than bonds (TLT) \u2014 investors in fear mode",
            v -> v < 3.0, "bonds more expensive than gold \u2014 calm market, normal",
            d -> d > 0, "fear rising \u2014 investors buying gold");

        check(byPair.get("XAU/HG1"), signals, "Capital Flows",
            "gold (XAU) more expensive than copper (HG1) \u2014 normal for uncertainty",
            v -> v < 8.0, "copper catching up to gold \u2014 risk appetite rising",
            d -> d > 0, "fear rising \u2014 gold rising faster than copper");

        check(byPair.get("NVDA/NG"), signals, "Capital Flows",
            "NVDA much more expensive than energy \u2014 AI bubble",
            v -> v < 40, "energy catching up to NVDA \u2014 AI bubble deflating",
            d -> d < 0, "AI euphoria fading \u2014 NVDA getting cheaper");

        // VERDICT
        long bullishCount = signals.stream().filter(Signal::isBullish).count();
        long bearishCount = signals.stream().filter(s -> !s.isBullish()).count();
        long total = signals.size();

        String verdictLabel;
        if (bearishCount > bullishCount + 2)
            verdictLabel = "\u001B[31m\u25BC Market cautious (" + bearishCount + "/" + total + ")\u001B[0m";
        else if (bullishCount > bearishCount + 2)
            verdictLabel = "\u001B[32m\u25B2 Base risk (" + bullishCount + "/" + total + ")\u001B[0m";
        else
            verdictLabel = "\u001B[33m\u25C6 Mixed (" + bullishCount + "B/" + bearishCount + "S)\u001B[0m";

        String summary = buildPlainSummary(signals, rows);

        return new Analysis(verdictLabel, signals, summary);
    }

    public static void printAll(List<MetricRow> frameworkRows) {
        Analysis a = analyze(frameworkRows);
        System.out.println("  " + DASH);
        System.out.println("  --- ANALYSIS SUMMARY (for non-specialist) ---");
        System.out.println("  " + DASH);
        System.out.println("  Rating: " + a.verdictLabel());
        System.out.println();

        Map<String,List<Signal>> byTheme = new LinkedHashMap<>();
        for (Signal s : a.signals()) {
            byTheme.computeIfAbsent(s.theme(), k -> new ArrayList<>()).add(s);
        }

        String[] order = {"Technology", "Market Mood", "Consumer", "Economy", "Credit", "Capital Flows"};

        for (String theme : order) {
            List<Signal> themeSignals = byTheme.get(theme);
            if (themeSignals == null || themeSignals.isEmpty()) continue;
            long good = themeSignals.stream().filter(Signal::isBullish).count();
            long bad = themeSignals.stream().filter(s -> !s.isBullish()).count();
            String status;
            if (bad == 0) status = "\u001B[32m\u2714\uFE0F all good\u001B[0m";
            else if (good == 0) status = "\u001B[31m\u274C problems\u001B[0m";
            else status = "\u001B[33m\u26A0\uFE0F mixed\u001B[0m";

            System.out.println("  " + theme + " " + status);
            for (Signal s : themeSignals) {
                String marker = s.isBullish() ? "  \u2705" : "  \u274C";
                System.out.println(marker + " " + stripEmoji(s.text()));
            }
            System.out.println();
        }

        System.out.println("  " + a.summary());
        System.out.println("  " + DASH);
    }

    private static String stripEmoji(String s) {
        return s.replace("\u2705", "").replace("\u274C", "").trim();
    }

    private static String buildPlainSummary(List<Signal> signals, List<MetricRow> rows) {
        long bearishCount = signals.stream().filter(s -> !s.isBullish()).count();
        long bullishCount = signals.stream().filter(s -> s.isBullish()).count();
        long total = signals.size();
        int downCount = countDirection(rows, "DOWN");
        StringBuilder sb = new StringBuilder();

        if (bearishCount > bullishCount + 2) {
            sb.append("Conclusion: " + bearishCount + "/" + total + " metrics point to problems. ");
            boolean hasCreditIssues = signals.stream().anyMatch(s -> s.theme().equals("Credit") && !s.isBullish());
            if (!hasCreditIssues) {
                sb.append("But credit market is still normal \u2014 this is a correction, not a crisis. ");
            }
            if (downCount > 10) {
                sb.append(downCount + "/" + rows.size() + " metrics in downtrend \u2014 typical of late cycle: leaders still holding but foundation weakening. ");
            }
            sb.append("Recommendation: reduce risk, prepare hedges.");
        } else if (bullishCount > bearishCount + 2) {
            sb.append("Conclusion: " + bullishCount + "/" + total + " metrics positive. Market is strong. ");
            sb.append("Trend up, but stay vigilant.");
        } else {
            if (downCount > 10) {
                sb.append("Mixed: " + downCount + "/" + rows.size() + " metrics declining. ");
                sb.append("Typical of late cycle \u2014 some sectors growing, others weakening. ");
            } else {
                sb.append("Signals balanced \u2014 market in consolidation. ");
            }
            sb.append("Key: watch HYG \u2014 if below 75, that is a credit crisis trigger.");
        }

        return sb.toString();
    }

    private static boolean contains(List<String> signals, String keyword) {
        return signals.stream().anyMatch(s -> s.contains(keyword));
    }

    private static int countDirection(List<MetricRow> rows, String dir) {
        return (int) rows.stream().filter(r -> dir.equals(r.dir())).count();
    }

    @FunctionalInterface interface LevelFn { boolean test(double v); }
    @FunctionalInterface interface DirFn { boolean test(double d); }

    private static void check(MetricRow r, List<Signal> signals, String theme,
                               String hiMsg, LevelFn lo, String loMsg,
                               DirFn dirBear, String dirMsg) {
        if (r == null) return;
        double cur = parseDouble(r.current());
        double prior = parseDouble(r.prior());
        boolean isDown = "DOWN".equals(r.dir());

        if (cur > 1.0) {
            if (Double.isNaN(cur) || cur <= 0) return;
        }

        if (lo != null && lo.test(cur)) {
            signals.add(new Signal(theme, loMsg + " [" + r.current() + "]", false));
        } else {
            signals.add(new Signal(theme, hiMsg + " [" + r.current() + "]", true));
        }

        if (!Double.isNaN(cur) && !Double.isNaN(prior) && Math.abs(cur - prior) / Math.max(Math.abs(prior), 0.001) > 0.005 && dirBear.test(cur - prior)) {
            signals.add(new Signal(theme, dirMsg + " (" + r.current() + " vs " + r.prior() + ")", false));
        }
    }

    private static void check(MetricRow r, List<Signal> signals, String theme,
                               String hiMsg, String loMsg,
                               DirFn dirBear, String dirMsg) {
        check(r, signals, theme, hiMsg, null, loMsg, dirBear, dirMsg);
    }

    private static double parseDouble(String s) {
        if (s == null || s.isEmpty() || s.equals("N/A") || s.equals("----")) return Double.NaN;
        try {
            return Double.parseDouble(s.replace(",", "."));
        } catch (NumberFormatException e) { return Double.NaN; }
    }
}
