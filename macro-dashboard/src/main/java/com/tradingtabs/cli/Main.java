package com.tradingtabs.cli;

import com.tradingtabs.model.DashboardData;
import com.tradingtabs.engine.*;
import com.tradingtabs.horizon.HorizonMatrix;
import com.tradingtabs.horizon.HorizonMatrix.*;
import com.tradingtabs.gann.*;
import java.io.PrintWriter;
import java.time.LocalDate;
import java.util.*;

public class Main {
    public static void main(String[] args) {
        boolean html = false;
        for (String a : args) {
            if (a.equals("--html") || a.equals("html")) html = true;
        }

        DataManager dm = new DataManager();
        DataManager.Snapshot snap = dm.fetchAll();

        MacroContext mc = new MacroContext(snap);
        MacroContext.MacroResult macro = mc.assess();

        BtcFrame bf = new BtcFrame(snap);
        BtcFrame.BtcResult btc = bf.assess();

        DivergenceScanner ds = new DivergenceScanner(snap);
        List<DivergenceScanner.Divergence> divs = ds.scan();

        HorizonMatrix hm = new HorizonMatrix();
        HorizonResult hr = hm.analyze(snap, macro, btc, divs);

        DashboardData dd = toDashboard(hr);
        printDashboard(dd);

        if (html) {
            try { writeHtml(dd); System.out.println("\n  HTML: dashboard.html"); }
            catch (Exception e) { System.err.println("  HTML failed: " + e.getMessage()); }
        }
    }

    static DashboardData toDashboard(HorizonResult hr) {
        DashboardData dd = new DashboardData();
        dd.date = hr.date();
        dd.btcPrice = hr.btcPrice();
        dd.fairValue = hr.fairValue();
        dd.metrics = hr.metrics();
        dd.shortTerm = hr.shortTerm();
        dd.mediumTerm = hr.mediumTerm();
        dd.longTerm = hr.longTerm();
        dd.micro = hr.micro();
        dd.frameworkRows = hr.frameworkRows();
        dd.scenarios = hr.scenarios();
        dd.divergences = hr.divergences();
        dd.macroStatus = hr.macroStatus();
        dd.btcStatus = hr.btcStatus();
        return dd;
    }

    // ─── CONSOLE ─────────────────────────────────────────────────────
    static void printDashboard(DashboardData dd) {
        String mC = color(dd.macroStatus), bC = color(dd.btcStatus);
        String title = "MACRO HORIZON \u2014 " + dd.date;
        System.out.println();
        System.out.println("  " + "\u2500".repeat(title.length() + 6));
        System.out.println("  " + title);
        System.out.println("  " + "\u2500".repeat(title.length() + 6));
        System.out.println();

        System.out.println("  BTC $" + String.format("%,.0f", dd.btcPrice) + "  |  Macro " + mC + dd.macroStatus + "\u001B[0m" +
            "  |  BTC " + bC + dd.btcStatus + "\u001B[0m");
        System.out.println();

        // METRIC TABLE
        System.out.println("  --- METRICS ---");
        System.out.printf("  %-22s %12s %12s %-5s %-2s %-6s  %s\n",
            "Metric", "Current", "Prior", "Unit", "Dir", "Horizon", "Note");
        int dashCount = Math.min(78, 22 + 12 + 12 + 5 + 2 + 6 + 12);
        System.out.println("  " + "\u2500".repeat(dashCount));
        for (MetricRow r : dd.metrics) {
            if (r.label().startsWith("--- ")) {
                System.out.println("  " + r.label());
            } else {
                System.out.printf("  %-22s %12s %12s %-5s %-2s %-6s  %s\n",
                    r.label(), r.current(), r.prior(), r.unit(), r.dir(), r.horizon(), r.note());
            }
        }
        System.out.println();

        // MICRO + FRAMEWORK
        if (dd.micro != null) {
            System.out.println("  --- MICRO CONDITIONS ---");
            String dash = "\u2500".repeat(46);
            System.out.println("  " + dash);
            System.out.printf("  %-16s %.1f  (%-12s)\n", "VIX", dd.micro.vix(), dd.micro.riskRegime());
            System.out.printf("  %-16s %s\n", "Sector", dd.micro.sectorSignal());
            StringBuilder sb = new StringBuilder();
            for (Map.Entry<String,Double> e : dd.micro.sector5d().entrySet()) {
                String sc = e.getValue() > 0 ? "\u001B[32m" : e.getValue() < 0 ? "\u001B[31m" : "\u001B[0m";
                sb.append(" ").append(e.getKey()).append(sc).append(String.format("%+.1f", e.getValue() * 100)).append("\u001B[0m");
            }
            System.out.printf("  %-16s %s\n", "Rotation", sb.toString());
            if (!Double.isNaN(dd.micro.bankPoverty()))
                System.out.printf("  %-16s %.2f pp\n", "Bank poverty", dd.micro.bankPoverty());
            System.out.println();

            // FRAMEWORK RATIOS — with Pair + Ref columns
            if (dd.frameworkRows != null && !dd.frameworkRows.isEmpty()) {
                System.out.println("  --- FRAMEWORK ---");
                System.out.printf("  %-17s %-11s %8s %8s %-4s %-4s %-7s  %s\n",
                    "Category", "Pair", "Current", "Prior", "Dir", "Hor", "Ref", "Note");
                System.out.println("  " + "\u2500".repeat(80));
                for (MetricRow r : dd.frameworkRows) {
                    System.out.printf("  %-17s %-11s %8s %8s %-4s %-4s %-7s  %s\n",
                        r.label(), r.pair(), r.current(), r.prior(), r.dir(), r.horizon(), r.ref(), r.note());
                }
            }
            System.out.println();
        }

        // SIGNAL SUMMARY — rule-based auto-analysis
        System.out.println();
        AutoAnalyzer.printAll(dd.frameworkRows);
        System.out.println();

        // GANN & PLANETARY BLOCK
        System.out.println();
        GannBlock.printAll(dd.btcPrice);
        System.out.println();

        // HORIZON OUTLOOK
        System.out.println("  --- OUTLOOK ---");
        System.out.println();
        printHorizonBox("SHORT (1-2w)", dd.shortTerm);
        System.out.println();
        printHorizonBox("MEDIUM (1-3m)", dd.mediumTerm);
        System.out.println();
        printHorizonBox("LONG (3-12m)", dd.longTerm);
        System.out.println();

        // DIVERGENCES
        if (dd.divergences != null && !dd.divergences.isEmpty()) {
            System.out.println("  --- DIVERGENCES ---");
            for (String div : dd.divergences) {
                System.out.println("    " + div);
            }
            System.out.println();
        }

        // SCENARIOS
        System.out.println("  --- SCENARIOS (1-3m) ---");
        for (Scenario s : dd.scenarios) {
            String sc = s.emoji().equals("GREEN") ? "\u001B[32m" : s.emoji().equals("RED") ? "\u001B[31m" : "\u001B[37m";
            System.out.printf("  %s%s (%d%%) %s\u001B[0m\n",
                sc, s.name(), (int)(s.prob() * 100), s.priceRange());
            System.out.println("    Trigger: " + s.trigger());
            System.out.println("    If: " + s.narrative());
            System.out.println();
        }

        // FOOTER
        String mC2 = color(dd.macroStatus), bC2 = color(dd.btcStatus);
        System.out.println("  " + "\u2500".repeat(50));
        System.out.printf("  Macro %s | BTC %s | %s | %s\n",
            mC2 + dd.macroStatus + "\u001B[0m", bC2 + dd.btcStatus + "\u001B[0m",
            dd.btcPrice > 0 ? "USD" : "", LocalDate.now());
    }

    static void printHorizonBox(String label, HorizonView hv) {
        String c = hv.status().contains("BULL") ? "\u001B[32m" : hv.status().contains("BEAR") ? "\u001B[31m" : hv.emoji().equals("YELLOW") ? "\u001B[33m" : "\u001B[37m";
        String badge = hv.emoji().equals("RED") ? "[BEAR]" : hv.emoji().equals("GREEN") ? "[BULL]" : hv.emoji().equals("YELLOW") ? "[MIX]" : "[--]";
        String boxColor = hv.emoji().equals("RED") ? "\u001B[31m" : hv.emoji().equals("GREEN") ? "\u001B[32m" : hv.emoji().equals("YELLOW") ? "\u001B[33m" : "\u001B[37m";
        int dash = Math.min(60, label.length() + 30);
        System.out.println("  " + boxColor + "\u2500".repeat(dash) + "\u001B[0m");
        System.out.println("  " + label + "  " + c + badge + " " + hv.status() + "\u001B[0m");
        System.out.println();
        for (String f : hv.factors()) {
            System.out.println("    > " + f);
        }
        System.out.println();
        System.out.println("  " + hv.summary());
        System.out.println("  " + boxColor + "\u2500".repeat(dash) + "\u001B[0m");
    }

    static String color(String status) {
        if (status == null) return "\u001B[37m";
        return switch (status) {
            case "GREEN" -> "\u001B[32m";
            case "RED" -> "\u001B[31m";
            case "YELLOW" -> "\u001B[33m";
            default -> "\u001B[37m";
        };
    }

    // ─── HTML ────────────────────────────────────────────────────────
    static void writeHtml(DashboardData dd) throws Exception {
        try (PrintWriter w = new PrintWriter("dashboard.html", "UTF-8")) {
            w.println("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">");
            w.println("<title>Macro Horizon</title><style>");
            w.println("body{background:#0a0a0f;color:#c8d0dc;font-family:'Consolas',monospace;padding:24px;max-width:960px;margin:auto}");
            w.println("h1{color:#e8d060;border-bottom:2px solid #e8d060;font-weight:400}");
            w.println("h2{color:#a0b0d0;font-weight:400;margin:20px 0 8px}");
            w.println(".green{color:#50ff90}.red{color:#ff5060}.yellow{color:#ffc040}");
            w.println(".section{background:#12121c;border:1px solid #2a2a3f;border-radius:6px;padding:12px 16px;margin:10px 0}");
            w.println("table{width:100%;border-collapse:collapse;font-size:13px}");
            w.println("th{text-align:left;color:#667;padding:4px 8px;border-bottom:1px solid #2a2a3f}");
            w.println("td{padding:4px 8px;border-bottom:1px solid #1a1a2a}");
            w.println(".boxes{display:flex;gap:8px}");
            w.println(".box{flex:1;background:#12121c;border:1px solid #2a2a3f;border-radius:6px;padding:10px}");
            w.println(".box h3{margin:0 0 6px;font-weight:400}");
            w.println(".status{font-size:18px;font-weight:bold}");
            w.println(".factors{font-size:12px;color:#8899bb;margin:6px 0}");
            w.println(".micro{font-size:12px;color:#8899bb;display:flex;gap:16px;flex-wrap:wrap}");
            w.println(".micro span{padding:4px 8px;background:#1a1a2a;border-radius:4px}");
            w.println(".scen{background:#12121c;border:1px solid #2a2a3f;border-radius:6px;padding:10px;margin:8px 0}");
            w.println(".scen h3{margin:0 0 4px;font-weight:400}");
            w.println(".trig{color:#8899bb;font-size:12px}");
            w.println(".meta{color:#445;font-size:10px;text-align:center;margin-top:24px}");
            w.println(".gann-section{background:#0f0f1a;border:1px solid #3a2a5f;border-radius:6px;padding:12px 16px;margin:10px 0}");
            w.println(".gann-section h2{color:#c8a0ff;border-bottom:1px solid #3a2a5f;padding-bottom:6px}");
            w.println(".planet-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;font-size:12px;margin:8px 0}");
            w.println(".planet-grid span{color:#aabbdd}");
            w.println(".aspect-item{font-size:12px;color:#99aacc;padding:2px 0}");
            w.println(".sq9-levels{font-size:12px;color:#8899bb}");
            w.println(".sq9-levels .res{color:#ff5060}.sq9-levels .sup{color:#50ff90}");
            w.println(".analysis-section{background:#0f1a0f;border:1px solid #2a4f2a;border-radius:6px;padding:12px 16px;margin:10px 0}");
            w.println(".analysis-section h2{color:#80d080;border-bottom:1px solid #2a4f2a;padding-bottom:6px}");
            w.println(".theme-row{margin:6px 0;font-size:12px}");
            w.println(".theme-name{font-weight:bold;margin-bottom:2px}");
            w.println(".sig{padding:1px 6px;margin:1px 0;display:inline-block;border-radius:3px;font-size:11px}");
            w.println(".sig-bull{background:#1a3a1a;color:#50ff90;border:1px solid #2a5f2a}");
            w.println(".sig-bear{background:#3a1a1a;color:#ff5060;border:1px solid #5f2a2a}");
            w.println(".verdict{font-size:15px;font-weight:bold;margin:8px 0;padding:6px 12px;border-radius:4px;display:inline-block}");
            w.println(".verdict-bull{background:#1a3a1a;color:#50ff90;border:1px solid #2a5f2a}");
            w.println(".verdict-bear{background:#3a1a1a;color:#ff5060;border:1px solid #5f2a2a}");
            w.println(".verdict-mix{background:#3a3a1a;color:#ffc040;border:1px solid #5f5f2a}");
            w.println(".astro-interp{font-size:12px;color:#bbaadd;margin:6px 0;padding:6px 10px;background:#1a1028;border-radius:4px;border:1px solid #2a2040}");
            w.println("</style></head><body>");
            w.println("<h1>MACRO HORIZON</h1>");
            w.printf("<p style=\"color:#667\">%s | BTC $%,.0f</p>", dd.date, dd.btcPrice);

            // Overview badges
            w.printf("<div style=\"margin:12px 0\">");
            w.printf("<span class=\"%s\" style=\"padding:4px 12px;border:1px solid;border-radius:4px;margin-right:6px\">Macro %s</span>",
                dd.macroStatus.toLowerCase(), dd.macroStatus);
            w.printf("<span class=\"%s\" style=\"padding:4px 12px;border:1px solid;border-radius:4px\">BTC %s</span>",
                dd.btcStatus.toLowerCase(), dd.btcStatus);
            w.println("</div>");

            // Metrics table
            w.println("<div class=\"section\"><table>");
            w.println("<tr><th>Metric</th><th>Current</th><th>Prior</th><th>Dir</th><th>Horizon</th><th>Note</th></tr>");
            for (MetricRow r : dd.metrics) {
                if (r.label().startsWith("--- ")) {
                    w.printf("<tr style=\"background:#1a1a2f\"><td colspan=\"6\"><b>%s</b></td></tr>", r.label());
                } else {
                    w.printf("<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"%s\">%s</td><td>%s</td><td>%s</td></tr>",
                        r.label(), r.current(), r.prior(), "yellow", r.dir(), r.horizon(), r.note());
                }
            }
            w.println("</table></div>");

            // MICRO section
            if (dd.micro != null) {
                w.println("<div class=\"section\">");
                w.println("<b>MICRO CONDITIONS</b>");
                w.println("<table>");
                w.printf("<tr><td>VIX</td><td>%.1f</td><td>%s</td></tr>", dd.micro.vix(), dd.micro.riskRegime());
                w.printf("<tr><td>Sector</td><td colspan=\"2\">%s</td></tr>", dd.micro.sectorSignal());
                w.print("<tr><td>Rotation</td><td colspan=\"2\">");
                for (Map.Entry<String,Double> e : dd.micro.sector5d().entrySet()) {
                    String sc = e.getValue() > 0 ? "green" : "red";
                    w.printf("<span class=\"%s\">%s %+.1f </span>", sc, e.getKey(), e.getValue() * 100);
                }
                w.println("</td></tr>");
                if (!Double.isNaN(dd.micro.bankPoverty()))
                    w.printf("<tr><td>Bank poverty</td><td>%.2f pp</td><td></td></tr>", dd.micro.bankPoverty());
                w.println("</table>");

                // FRAMEWORK RATIOS
                if (dd.frameworkRows != null && !dd.frameworkRows.isEmpty()) {
                    w.println("<table style=\"margin-top:6px\">");
                    w.println("<tr style=\"color:#667\"><th style=\"text-align:left\">Category</th><th style=\"text-align:left\">Pair</th><th style=\"text-align:right\">Current</th><th style=\"text-align:right\">Prior</th><th>Dir</th><th>Hor</th><th style=\"text-align:center\">Ref</th><th>Note</th></tr>");
                    for (MetricRow r : dd.frameworkRows) {
                        w.printf("<tr><td>%s</td><td style=\"color:#556\">%s</td><td style=\"text-align:right\">%s</td><td style=\"text-align:right\">%s</td><td>%s</td><td>%s</td><td style=\"text-align:center;color:#667\">%s</td><td>%s</td></tr>",
                            r.label(), r.pair(), r.current(), r.prior(), r.dir(), r.horizon(), r.ref(), r.note());
                    }
                    w.println("</table>");
                }
                w.println("</div>");
            }

            // ANALYSIS SUMMARY (AutoAnalyzer)
            if (dd.frameworkRows != null && !dd.frameworkRows.isEmpty()) {
                AutoAnalyzer.Analysis analysis = AutoAnalyzer.analyze(dd.frameworkRows);
                long bearishCount = analysis.signals().stream().filter(s -> !s.isBullish()).count();
                long bullishCount = analysis.signals().stream().filter(AutoAnalyzer.Signal::isBullish).count();
                long total = analysis.signals().size();

                w.println("<div class=\"analysis-section\">");
                w.println("<h2>ANALYSIS SUMMARY</h2>");

                String verdictClass, verdictText;
                if (bearishCount > bullishCount + 2) {
                    verdictClass = "verdict-bear";
                    verdictText = "&#9660; Market cautious (" + bearishCount + "/" + total + ")";
                } else if (bullishCount > bearishCount + 2) {
                    verdictClass = "verdict-bull";
                    verdictText = "&#9650; Base risk (" + bullishCount + "/" + total + ")";
                } else {
                    verdictClass = "verdict-mix";
                    verdictText = "&#9670; Mixed (" + bullishCount + "B/" + bearishCount + "S)";
                }
                w.printf("<div class=\"verdict %s\">%s</div>%n", verdictClass, verdictText);

                Map<String, List<AutoAnalyzer.Signal>> byTheme = new LinkedHashMap<>();
                for (AutoAnalyzer.Signal s : analysis.signals()) {
                    byTheme.computeIfAbsent(s.theme(), k -> new ArrayList<>()).add(s);
                }
                String[] themeOrder = {"Technology", "Market Mood", "Consumer", "Economy", "Credit", "Capital Flows"};
                for (String theme : themeOrder) {
                    List<AutoAnalyzer.Signal> ts = byTheme.get(theme);
                    if (ts == null || ts.isEmpty()) continue;
                    long good = ts.stream().filter(AutoAnalyzer.Signal::isBullish).count();
                    long bad = ts.stream().filter(s -> !s.isBullish()).count();
                    String icon = bad == 0 ? "&#10004;" : good == 0 ? "&#10060;" : "&#9888;";
                    w.printf("<div class=\"theme-row\"><div class=\"theme-name\">%s %s</div>%n", theme, icon);
                    for (AutoAnalyzer.Signal s : ts) {
                        String cls = s.isBullish() ? "sig-bull" : "sig-bear";
                        String m = s.isBullish() ? "&#10004;" : "&#10060;";
                        w.printf("<div class=\"sig %s\">%s %s</div>%n", cls, m, s.text());
                    }
                    w.println("</div>");
                }
                w.printf("<div style=\"font-size:12px;color:#8899bb;margin-top:8px\">%s</div>%n", analysis.summary());
                w.println("</div>");
            }

            // GANN & PLANETARY
            {
                LocalDate today = LocalDate.now();
                double jd = Ephemeris.toJulianDay(today);
                Map<Ephemeris.Planet, Ephemeris.GeoPos> pos = Ephemeris.compute(today);

                w.println("<div class=\"gann-section\">");
                w.println("<h2>GANN &amp; PLANETARY</h2>");

                // Lunar
                int lDay = Ephemeris.lunarDay(jd);
                String phase = Ephemeris.moonPhaseName(jd);
                double illum = Ephemeris.moonIllumination(jd);
                String sent;
                if (lDay <= 1) sent = "volatile (new moon)";
                else if (lDay == 14 || lDay == 15) sent = "volatile (full moon)";
                else if (lDay == 7 || lDay == 8) sent = "directional (first qtr)";
                else if (lDay == 22 || lDay == 23) sent = "directional (last qtr)";
                else if (lDay < 14) sent = "expansive (waxing)";
                else sent = "contractive (waning)";
                w.printf("<div>Lunar day: <b>%d</b> (%s, %.0f%% illuminated) &mdash; Market: <b>%s</b></div>%n",
                    lDay, phase, illum * 100, sent);

                // Planetary positions
                w.println("<div style=\"margin-top:8px\"><b>Planetary positions (geocentric ecliptic):</b></div>");
                w.println("<div class=\"planet-grid\">");
                for (Ephemeris.Planet p : Ephemeris.Planet.values()) {
                    Ephemeris.GeoPos gp = pos.get(p);
                    if (gp == null) continue;
                    String sign = GannBlock.zodiacSign(gp.longitude());
                    w.printf("<span>%-8s %6.1f&deg; %s (lat: %+.1f&deg;)</span>%n",
                        p, gp.longitude(), sign, gp.latitude());
                }
                w.println("</div>");

                // Aspects today
                List<AspectFinder.Aspect> todayAspects = AspectFinder.findAspects(pos, 6.0);
                if (!todayAspects.isEmpty()) {
                    w.println("<div style=\"margin-top:8px\"><b>Aspects today:</b></div>");
                    for (AspectFinder.Aspect a : todayAspects) {
                        w.printf("<div class=\"aspect-item\">%s</div>%n", a.label());
                    }
                }

                // Upcoming aspects
                Map<LocalDate, List<AspectFinder.Aspect>> upcoming = AspectFinder.scanForwardGrouped(today, 14, 3.0);
                if (!upcoming.isEmpty()) {
                    w.println("<div style=\"margin-top:8px\"><b>Upcoming aspects (14d, orb &plusmn;3&deg;):</b></div>");
                    int cnt = 0;
                    java.time.format.DateTimeFormatter fmt = java.time.format.DateTimeFormatter.ofPattern("dd MMM", java.util.Locale.ENGLISH);
                    for (Map.Entry<LocalDate, List<AspectFinder.Aspect>> e : upcoming.entrySet()) {
                        if (e.getKey().equals(today)) continue;
                        if (cnt >= 8) { w.println("<div class=\"aspect-item\">...</div>"); break; }
                        for (AspectFinder.Aspect a : e.getValue()) {
                            w.printf("<div class=\"aspect-item\">%s &rarr; %s</div>%n", e.getKey().format(fmt), a.label());
                            cnt++;
                        }
                    }
                }

                // Astrological interpretation
                double jupLon = GannBlock.getLon(pos, Ephemeris.Planet.JUPITER);
                double satLon = GannBlock.getLon(pos, Ephemeris.Planet.SATURN);
                double marsLon = GannBlock.getLon(pos, Ephemeris.Planet.MARS);
                double uranLon = GannBlock.getLon(pos, Ephemeris.Planet.URANUS);

                w.println("<div class=\"astro-interp\">");
                w.print("<b>&#1054;&#1082;&#1086;&#1085;&#1092;&#1080;&#1075;&#1091;&#1088;&#1072;&#1094;&#1080;&#1103;:</b> &#1057;&#1086;&#1083;&#1085;&#1094;&#1077; &#1074; &#1056;&#1072;&#1082;&#1077; (&#1079;&#1072;&#1097;&#1080;&#1090;&#1072;/&#1085;&#1086;&#1089;&#1090;&#1072;&#1083;&#1100;&#1075;&#1080;&#1103;)");
                if (jupLon >= 90 && jupLon < 120) w.print(", &#1070;&#1087;&#1080;&#1090;&#1077;&#1088; &#1074; &#1056;&#1072;&#1082;&#1077; (&#1085;&#1072;&#1082;&#1086;&#1087;&#1083;&#1077;&#1085;&#1080;&#1077;/&#1080;&#1079;&#1073;&#1099;&#1090;&#1086;&#1082;)");
                if (satLon >= 0 && satLon < 30) w.print(", &#1057;&#1072;&#1090;&#1091;&#1088;&#1085; &#1074; &#1054;&#1074;&#1085;&#1077; (&#1086;&#1075;&#1088;&#1072;&#1085;&#1080;&#1095;&#1077;&#1085;&#1080;&#1103;/&#1090;&#1077;&#1089;&#1090;)");
                if (marsLon >= 30 && marsLon < 60) w.print(", &#1052;&#1072;&#1088;&#1089; &#1074; &#1058;&#1077;&#1083;&#1100;&#1094;&#1077; (&#1091;&#1087;&#1088;&#1103;&#1084;&#1089;&#1090;&#1074;&#1086;/&#1089;&#1090;&#1086;&#1080;&#1084;&#1086;&#1089;&#1090;&#1100;)");
                if (uranLon >= 60 && uranLon < 90) w.print(", &#1059;&#1088;&#1072;&#1085; &#1074; &#1041;&#1083;&#1080;&#1079;&#1085;&#1077;&#1094;&#1072;&#1093; (&#1080;&#1085;&#1085;&#1086;&#1074;&#1072;&#1094;&#1080;&#1080;/&#1093;&#1072;&#1086;&#1089;)");
                w.println();

                boolean hasKeyInterp = false;
                for (AspectFinder.Aspect a : todayAspects) {
                    if (a.orbUsed() < 3.0) {
                        String interp = GannBlock.aspectInterpretation(a);
                        if (interp != null) { w.printf("<div>%s</div>%n", interp); hasKeyInterp = true; }
                    }
                }
                if (!hasKeyInterp) {
                    for (AspectFinder.Aspect a : todayAspects) {
                        if (a.orbUsed() < 2.0) {
                            String interp = GannBlock.aspectInterpretation(a);
                            if (interp != null) w.printf("<div>%s</div>%n", interp);
                        }
                    }
                }

                if (lDay < 14) w.println("<div>&#1060;&#1072;&#1079;&#1072; &#1088;&#1086;&#1089;&#1090;&#1072; &mdash; &#1088;&#1099;&#1085;&#1086;&#1082; &#1089;&#1082;&#1083;&#1086;&#1085;&#1077;&#1085; &#1082; &#1088;&#1072;&#1089;&#1096;&#1080;&#1088;&#1077;&#1085;&#1080;&#1102;.</div>");
                else w.println("<div>&#1060;&#1072;&#1079;&#1072; &#1091;&#1073;&#1099;&#1074;&#1072;&#1085;&#1080;&#1103; &mdash; &#1088;&#1099;&#1085;&#1086;&#1082; &#1089;&#1082;&#1083;&#1086;&#1085;&#1077;&#1085; &#1082; &#1089;&#1078;&#1072;&#1090;&#1080;&#1102;.</div>");
                if (lDay >= 12 && lDay <= 16)
                    w.println("<div>&#1041;&#1083;&#1080;&#1078;&#1077; &#1082; &#1087;&#1086;&#1083;&#1085;&#1086;&#1083;&#1091;&#1085;&#1080;&#1102; &mdash; &#1074;&#1086;&#1079;&#1084;&#1086;&#1078;&#1085;&#1099; &#1088;&#1077;&#1079;&#1082;&#1080;&#1077; &#1076;&#1074;&#1080;&#1078;&#1077;&#1085;&#1080;&#1103;.</div>");
                w.println("<div>Gann Square of 9: &#1094;&#1077;&#1085;&#1072; &#1084;&#1077;&#1078;&#1076;&#1091; &#1082;&#1074;&#1072;&#1076;&#1088;&#1072;&#1090;&#1072;&#1084;&#1080; &mdash; &#1079;&#1086;&#1085;&#1072; &#1085;&#1077;&#1086;&#1087;&#1088;&#1077;&#1076;&#1077;&#1083;&#1105;&#1085;&#1085;&#1086;&#1089;&#1090;&#1080;.</div>");
                w.println("</div>");

                // Square of 9
                w.println("<div style=\"margin-top:8px\"><b>SQUARE OF 9 (BTC):</b></div>");
                w.println("<div class=\"sq9-levels\">");
                double sqAngle = GannSquare9.priceToAngle(dd.btcPrice);
                double sqSqrt = Math.sqrt(dd.btcPrice);
                int sqRing = (int)((sqSqrt + 1) / 2);
                if (sqRing < 1) sqRing = 1;
                w.printf("<div>Price: $%,.0f | Ring: %d | Angle: %.1f&deg;</div>%n", dd.btcPrice, sqRing, sqAngle);

                List<GannSquare9.Level> levels = GannSquare9.getSupportResistance(dd.btcPrice, 3, 3);
                int lvlCnt = 0;
                for (GannSquare9.Level l : levels) {
                    if (lvlCnt >= 6) break;
                    String cls = l.price() > dd.btcPrice ? "res" : "sup";
                    String marker = l.price() > dd.btcPrice ? "R" : "S";
                    double pct = (l.price() - dd.btcPrice) / dd.btcPrice * 100;
                    w.printf("<div class=\"%s\">%s $%,.0f (%.1f%%)</div>%n", cls, marker, l.price(), pct);
                    lvlCnt++;
                }
                w.println("</div>");
                w.println("</div>");
            }

            // Horizons
            w.println("<div class=\"boxes\">");
            writeHtmlHorizon(w, "SHORT 1-2w", dd.shortTerm);
            writeHtmlHorizon(w, "MEDIUM 1-3m", dd.mediumTerm);
            writeHtmlHorizon(w, "LONG 3-12m", dd.longTerm);
            w.println("</div>");

            // Divergences
            if (dd.divergences != null && !dd.divergences.isEmpty()) {
                w.println("<div class=\"section\"><b>DIVERGENCES</b><br>");
                for (String div : dd.divergences) {
                    w.println("<div style=\"font-size:13px;padding:2px 0\">" + div + "</div>");
                }
                w.println("</div>");
            }

            // Scenarios
            w.println("<h2>SCENARIOS (1-3 months)</h2>");
            for (Scenario s : dd.scenarios) {
                String sc = s.emoji().equals("GREEN") ? "green" : s.emoji().equals("RED") ? "red" : "yellow";
                w.printf("<div class=\"scen\">");
                w.printf("<h3 class=\"%s\">%s <span style=\"float:right\">%d%% &mdash; %s</span></h3>",
                    sc, s.name(), (int)(s.prob()*100), s.priceRange());
                w.printf("<div class=\"trig\">Trigger: %s</div>", s.trigger());
                w.printf("<div class=\"trig\">If: %s</div>", s.narrative());
                w.println("</div>");
            }

            w.println("<div class=\"meta\">FRED + Yahoo Finance + Binance &middot; " + LocalDate.now() + "</div>");
            w.println("</body></html>");
        }
    }

    static String fmtHtmlVal(String tk, double v) {
        if (v > 100) return String.format("%.0f", v);
        if (v > 10) return String.format("%.1f", v);
        return String.format("%.2f", v);
    }

    static void writeHtmlHorizon(PrintWriter w, String label, HorizonView hv) {
        String sc = hv.emoji().equals("GREEN") ? "green" : hv.emoji().equals("RED") ? "red" : "yellow";
        String badge = hv.emoji().equals("RED") ? "[BEAR]" : hv.emoji().equals("GREEN") ? "[BULL]" : hv.emoji().equals("YELLOW") ? "[MIX]" : "[--]";
        w.printf("<div class=\"box\">");
        w.printf("<h3>%s</h3>", label);
        w.printf("<div class=\"status %s\">%s %s</div>", sc, badge, hv.status());
        w.println("<div class=\"factors\">");
        for (String f : hv.factors()) w.println("> " + f + "<br>");
        w.println("</div>");
        w.printf("<div style=\"font-size:11px;color:#667;margin-top:6px\">%s</div>", hv.summary());
        w.println("</div>");
    }
}
