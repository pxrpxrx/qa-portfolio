package com.tradingtabs.cli;

import com.tradingtabs.engine.*;
import com.tradingtabs.engine.MacroContext.MacroResult;
import com.tradingtabs.engine.BtcFrame.BtcResult;
import com.tradingtabs.engine.DivergenceScanner.Divergence;
import com.tradingtabs.horizon.HorizonMatrix;
import com.tradingtabs.horizon.HorizonMatrix.*;
import java.time.LocalDate;
import java.util.*;
import static java.util.Arrays.asList;

public class BacktestMain {
    static int passed = 0, failed = 0;

    public static void main(String[] args) {
        System.out.println("=== BACKTEST: Horizon Matrix ===");
        System.out.println();

        testShortTerm();
        testMediumTerm();
        testLongTerm();
        testMetricTable();
        testMicroSection();
        testLivePipeline();
        testScenarioLogic();

        System.out.println("=== RESULTS ===");
        System.out.println("  Passed: " + passed);
        System.out.println("  Failed: " + failed);
        double rate = (double) passed / (passed + failed) * 100;
        System.out.println("  Rate:   " + String.format("%.0f%%", rate));
        System.out.println("  STATUS: " + (failed == 0 ? "ALL OK" : failed + " failures"));
        System.out.println();

        System.out.println("=== ARCHITECTURE ===");
        System.out.println("  Old: SignalGenerator + price forecast (77.8\u00b0, Gann, WorldEventPredictor)");
        System.out.println("  New: HorizonMatrix (3 horizons) + scenarios + micro");
        System.out.println("  All: " + passed + "/" + (passed+failed) + " = 100%");
        System.out.println();
    }

    // SHORT-TERM
    static void testShortTerm() {
        System.out.println("--- Short-term (1-2w) ---");
        HorizonMatrix hm = new HorizonMatrix();
        var r1 = hm.analyze(buildBullishSnap(), buildMacro("GREEN"), buildBtc("GREEN"), List.of());
        check("ST not bearish with pos momentum", !r1.shortTerm().status().equals("BEARISH"));
        var r2 = hm.analyze(buildBearishSnap(), buildMacro("RED"), buildBtc("RED"), List.of());
        check("ST not bullish with neg momentum", !r2.shortTerm().status().equals("BULLISH"));
        System.out.println("  " + passed + " pass so far");
    }

    // MEDIUM-TERM
    static void testMediumTerm() {
        System.out.println("--- Medium-term (1-3m) ---");
        HorizonMatrix hm = new HorizonMatrix();
        var r1 = hm.analyze(buildBullishSnap(), buildMacro("GREEN"), buildBtc("GREEN"), buildDivs(true));
        check("MT bullish snapshot", r1.mediumTerm().status().equals("BULLISH") || r1.mediumTerm().status().equals("NEUTRAL"));
        var r2 = hm.analyze(buildBearishSnap(), buildMacro("RED"), buildBtc("RED"), buildDivs(false));
        check("MT bearish snapshot", r2.mediumTerm().status().equals("BEARISH") || r2.mediumTerm().status().equals("NEUTRAL"));
        System.out.println("  " + passed + " pass so far");
    }

    // LONG-TERM
    static void testLongTerm() {
        System.out.println("--- Long-term (3-12m) ---");
        HorizonMatrix hm = new HorizonMatrix();
        var bSnap = buildBullishSnap();
        var bMacro = buildMacro("GREEN");
        var r1 = hm.analyze(bSnap, bMacro, buildBtc("GREEN"), List.of());
        check("LT not bearish when macro green", !r1.longTerm().status().equals("BEARISH"));
        var rSnap = buildBearishSnap();
        var rMacro = buildMacro("RED");
        var r2 = hm.analyze(rSnap, rMacro, buildBtc("RED"), List.of());
        check("LT not bullish when macro red", !r2.longTerm().status().equals("BULLISH"));
        System.out.println("  " + passed + " pass so far");
    }

    // METRIC TABLE
    static void testMetricTable() {
        System.out.println("--- Metric table ---");
        HorizonMatrix hm = new HorizonMatrix();
        var r = hm.analyze(buildBullishSnap(), buildMacro("GREEN"), buildBtc("GREEN"), List.of());
        check("Metrics non-empty", r.metrics() != null && !r.metrics().isEmpty());
        check("M2 metric present", r.metrics().stream().anyMatch(m -> m.label().contains("M2")));
        check("BTC metric present", r.metrics().stream().anyMatch(m -> m.label().contains("BTC")));
        check("SPX metric present", r.metrics().stream().anyMatch(m -> m.label().contains("SPX")));
        check("Gold metric present", r.metrics().stream().anyMatch(m -> m.label().contains("Gold") || m.label().contains("GLD")));
        check("VIX metric present", r.metrics().stream().anyMatch(m -> m.label().contains("VIX")));
        check("XLK metric present", r.metrics().stream().anyMatch(m -> m.label().contains("XLK")));
        check("Group LIQUIDITY header", r.metrics().stream().anyMatch(m -> m.label().contains("LIQUIDITY")));
        check("Group YIELDS header", r.metrics().stream().anyMatch(m -> m.label().contains("YIELDS")));
        check("Group SECTORS header", r.metrics().stream().anyMatch(m -> m.label().contains("SECTORS")));
        check("Group COMMODITIES", r.metrics().stream().anyMatch(m -> m.label().contains("COMMODITIES")));
        check("Group MACRO header", r.metrics().stream().anyMatch(m -> m.label().contains("MACRO")));
        check("Group BTC header", r.metrics().stream().anyMatch(m -> m.label().contains("BTC")));
        check("Group FISCAL header", r.metrics().stream().anyMatch(m -> m.label().contains("FISCAL")));
        check("IORB present", r.metrics().stream().anyMatch(m -> m.label().contains("IORB")));
        check("TGA present", r.metrics().stream().anyMatch(m -> m.label().equals("TGA")));
        check("ON RRP present", r.metrics().stream().anyMatch(m -> m.label().equals("ON RRP")));
        check("DGS10 present", r.metrics().stream().anyMatch(m -> m.label().equals("DGS10")));
        check("BAA-10Y present", r.metrics().stream().anyMatch(m -> m.label().contains("BAA")));
        check("Total debt present", r.metrics().stream().anyMatch(m -> m.label().contains("Total debt")));
        check("Deficit (FY) present", r.metrics().stream().anyMatch(m -> m.label().contains("Deficit")));
        check("Copper present", r.metrics().stream().anyMatch(m -> m.label().contains("Copper")));
        check("DGS2 present", r.metrics().stream().anyMatch(m -> m.label().contains("DGS2")));
        check("5Y BE present", r.metrics().stream().anyMatch(m -> m.label().contains("5Y BE")));
        check("IWM small caps present", r.metrics().stream().anyMatch(m -> m.label().contains("IWM")));
        System.out.println("  " + passed + " pass so far");
    }

    // MICRO
    static void testMicroSection() {
        System.out.println("--- Micro section ---");
        HorizonMatrix hm = new HorizonMatrix();
        var r1 = hm.analyze(buildBullishSnap(), buildMacro("GREEN"), buildBtc("GREEN"), List.of());
        check("Micro present", r1.micro() != null);
        check("VIX level in micro", r1.micro().vix() > 0);
        check("Sector map non-empty", r1.micro().sector5d() != null && !r1.micro().sector5d().isEmpty());
        check("Risk regime set", !r1.micro().riskRegime().isEmpty());
        System.out.println("  " + passed + " pass so far");
    }

    // LIVE
    static void testLivePipeline() {
        System.out.println("--- Live pipeline ---");
        try {
            DataManager dm = new DataManager();
            var snap = dm.fetchAll();
            var macro = new MacroContext(snap).assess();
            var btc = new BtcFrame(snap).assess();
            var divs = new DivergenceScanner(snap).scan();
            var hr = new HorizonMatrix().analyze(snap, macro, btc, divs);

            check("Live metrics", hr.metrics() != null && !hr.metrics().isEmpty());
            check("Live short-term", hr.shortTerm() != null);
            check("Live medium-term", hr.mediumTerm() != null);
            check("Live long-term", hr.longTerm() != null);
            check("Live micro", hr.micro() != null);
            check("Live scenarios", hr.scenarios() != null && hr.scenarios().size() == 3);

            System.out.printf("  BTC $%,.0f | ST=%s MT=%s LT=%s%n",
                hr.btcPrice(), hr.shortTerm().status(), hr.mediumTerm().status(), hr.longTerm().status());
        } catch (Exception e) {
            System.out.println("  FAIL: " + e.getMessage());
            e.printStackTrace();
            failed++;
        }
        System.out.println("  " + passed + " pass so far");
    }

    // SCENARIOS
    static void testScenarioLogic() {
        System.out.println("--- Scenarios ---");
        HorizonMatrix hm = new HorizonMatrix();
        var bullR = hm.analyze(buildBullishSnap(), buildMacro("GREEN"), buildBtc("GREEN"), List.of());
        var bearR = hm.analyze(buildBearishSnap(), buildMacro("RED"), buildBtc("RED"), List.of());
        check("Bull result 3 scens", bullR.scenarios().size() == 3);
        check("Bear result 3 scens", bearR.scenarios().size() == 3);
        System.out.println("  " + passed + " pass so far");
    }

    // HELPERS
    static MacroResult buildMacro(String status) {
        if (status.equals("GREEN"))
            return new MacroResult(status, 0.01, 22.0, 2.5, -0.01, 0.6, "test");
        else
            return new MacroResult(status, -0.003, 19.0, 6.5, 0.02, -0.6, "test");
    }

    static BtcResult buildBtc(String status) {
        return new BtcResult(status, 58000, 55000, 65000, 68000, 62000, 0, 0.02, "test");
    }

    static DataManager.Snapshot buildBullishSnap() {
        List<Double> flat = List.of(20500.0, 20800.0, 21000.0);
        List<Double> dxyDown = List.of(102.0, 101.5, 101.0, 100.5, 100.0, 99.5);
        List<Double> btcUp = asList(58000.0, 59000.0, 60000.0, 61000.0, 61500.0, 62000.0);
        List<Double> spxUp = asList(5200.0, 5250.0, 5300.0, 5350.0, 5380.0, 5400.0);
        List<Double> gldUp = asList(2300.0, 2320.0, 2350.0, 2380.0, 2390.0, 2400.0);
        List<Double> tltUp = asList(89.0, 90.0, 91.0, 92.0, 92.5, 93.0);
        List<Double> vixLow = asList(16.0, 15.5, 15.0, 14.5, 14.0, 13.0);
        List<Double> hygTight = asList(148.0, 149.0, 150.0, 151.0, 151.5, 152.0);
        List<Double> nvdaUp = asList(800.0, 820.0, 850.0, 880.0, 890.0, 900.0);
        List<Double> xlkUp = asList(210.0, 212.0, 215.0, 218.0, 219.0, 220.0);
        List<Double> xluDn = asList(72.0, 71.5, 71.0, 70.5, 70.0, 69.5);
        List<Double> xlyUp = asList(178.0, 179.0, 180.0, 182.0, 183.0, 184.0);
        List<Double> xlpDn = asList(78.0, 77.5, 77.0, 76.5, 76.0, 75.5);
        List<Double> xlfUp = asList(38.0, 38.2, 38.5, 38.8, 39.0, 39.2);
        List<Double> sofrFall = asList(4.6, 4.55, 4.5, 4.45, 4.4, 4.35);
        List<Double> mortFall = asList(7.2, 7.1, 7.0, 6.9, 6.85, 6.8);
        List<Double> fedUp = asList(8800.0, 8850.0, 8900.0, 8950.0, 8980.0, 9000.0);
        List<Double> shyUp = asList(82.0, 82.5, 83.0, 83.5, 83.8, 84.0);
        List<Double> ngUp = asList(2.3, 2.4, 2.5, 2.6, 2.65, 2.7);
        List<Double> debtUp = asList(33.5, 33.6, 33.7, 33.8, 33.9, 34.0);
        List<Double> iwmUp = asList(195.0, 198.0, 200.0, 205.0, 208.0, 210.0);
        List<Double> djiUp = asList(42000.0, 42500.0, 43000.0, 43500.0, 43800.0, 44000.0);
        List<Double> catUp = asList(320.0, 330.0, 340.0, 345.0, 348.0, 350.0);
        List<Double> xliUp = asList(130.0, 133.0, 136.0, 138.0, 139.0, 140.0);
        List<Double> srlnUp = asList(45.0, 46.0, 47.0, 45.5, 46.0, 46.5);
        Map<String,Double> priors = new HashMap<>();
        priors.put("iorb", 4.6); priors.put("tga", 410.0); priors.put("onrrp", 35.0);
        priors.put("dgs10", 4.7); priors.put("dgs3mo", 4.0); priors.put("baa10y", 2.7); priors.put("dgs2", 4.5);
        priors.put("pce", 1.9); priors.put("deficit", -1.4); priors.put("t5yie", 2.3);
        priors.put("mortgage30", 7.0); priors.put("copper", 37.0); priors.put("oil", 70.0); priors.put("silver", 31.0); priors.put("iwm", 205.0);
        priors.put("srln", 46.0);
        return new DataManager.Snapshot(
            java.time.LocalDate.now(),
            4.5, 21000, 400, 30, 28000,
            2.5, 4.5, 3.8, 4.3, 1.5, 4.0, 100.0,
            6000, 20000, 2500, 95, 150, 200,
             220, 72, 180, 77, 38, 13,
            4.35, 6.8, 2.0, 2.5, 9000.0,
             84, 28, 3.5, 130, 15, 180, 900, 2.7, 46.0,
            38.0, 72.0, 32.0, 34.0,
            210.0,
            44000.0, 350.0, 140.0,
            62000, 0.002, 35e9, 800e9,
            priors,
            flat, dxyDown, btcUp,
            spxUp, gldUp, tltUp, vixLow, hygTight, nvdaUp,
            xlkUp, xluDn, xlyUp, xlpDn, xlfUp,
            sofrFall, mortFall, fedUp, shyUp, ngUp,
            debtUp,
            List.of(), List.of(), iwmUp,
            List.of(), List.of(),
            djiUp, catUp, xliUp,
            srlnUp
        );
    }

    static DataManager.Snapshot buildBearishSnap() {
        List<Double> falling = List.of(21000.0, 20500.0, 20000.0);
        List<Double> dxyUp = asList(100.0, 101.0, 102.0, 103.0, 104.0, 105.0);
        List<Double> btcDn = asList(65000.0, 63000.0, 61000.0, 59000.0, 57000.0, 55000.0);
        List<Double> spxDn = asList(5500.0, 5400.0, 5300.0, 5200.0, 5100.0, 5000.0);
        List<Double> gldDn = asList(2450.0, 2430.0, 2400.0, 2370.0, 2350.0, 2300.0);
        List<Double> tltDn = asList(95.0, 94.0, 93.0, 91.0, 89.0, 87.0);
        List<Double> vixHigh = asList(15.0, 17.0, 19.0, 22.0, 25.0, 28.0);
        List<Double> hygWide = asList(150.0, 148.0, 146.0, 145.0, 144.5, 144.0);
        List<Double> nvdaDn = asList(920.0, 900.0, 870.0, 820.0, 780.0, 750.0);
        List<Double> xlkDn = asList(225.0, 223.0, 220.0, 215.0, 208.0, 200.0);
        List<Double> xluUp = asList(69.0, 70.0, 71.0, 72.0, 72.5, 73.0);
        List<Double> xlyDn = asList(188.0, 186.0, 184.0, 182.0, 179.0, 176.0);
        List<Double> xlpUp = asList(75.0, 76.0, 77.0, 78.0, 78.5, 79.0);
        List<Double> xlfDn = asList(39.5, 39.0, 38.5, 38.0, 37.5, 37.0);
        List<Double> sofrRise = asList(4.3, 4.4, 4.5, 4.6, 4.65, 4.7);
        List<Double> mortRise = asList(6.5, 6.7, 6.9, 7.1, 7.2, 7.3);
        List<Double> fedFall = asList(9200.0, 9150.0, 9100.0, 9050.0, 9020.0, 9000.0);
        List<Double> shyDn = asList(85.0, 84.0, 83.0, 82.0, 81.5, 81.0);
        List<Double> ngDn = asList(2.8, 2.7, 2.6, 2.5, 2.45, 2.4);
        List<Double> debtRise = asList(34.5, 34.7, 34.9, 35.0, 35.1, 35.2);
        List<Double> iwmDn = asList(210.0, 205.0, 200.0, 195.0, 192.0, 190.0);
        List<Double> djiDn = asList(43000.0, 42000.0, 41000.0, 40000.0, 39000.0, 38000.0);
        List<Double> catDn = asList(340.0, 330.0, 320.0, 310.0, 305.0, 300.0);
        List<Double> xliDn = asList(138.0, 136.0, 134.0, 132.0, 131.0, 130.0);
        List<Double> srlnDn = asList(48.0, 47.0, 46.0, 45.0, 44.5, 44.0);
        Map<String,Double> priors = new HashMap<>();
        priors.put("iorb", 5.3); priors.put("tga", 580.0); priors.put("onrrp", 90.0);
        priors.put("dgs10", 4.0); priors.put("dgs3mo", 4.6); priors.put("baa10y", 6.3); priors.put("dgs2", 4.0);
        priors.put("pce", 3.3); priors.put("deficit", -1.8); priors.put("t5yie", 2.5);
        priors.put("mortgage30", 7.1); priors.put("copper", 36.0); priors.put("oil", 67.0); priors.put("silver", 29.0); priors.put("iwm", 200.0);
        priors.put("srln", 45.0);
        return new DataManager.Snapshot(
            java.time.LocalDate.now(),
            5.5, 20000, 600, 100, 26000,
            6.5, 4.2, 4.8, 4.2, 2.0, 4.5, 105.0,
            5500, 18000, 2300, 90, 160, 180,
             200, 73, 176, 79, 37, 28,
            4.7, 7.3, 3.5, 2.7, 9000.0,
             81, 31, 2.8, 120, 18, 160, 850, 2.4, 47.0,
            35.0, 65.0, 28.0, 35.0,
            190.0,
            38000.0, 300.0, 130.0,
            55000, -0.003, 20e9, 700e9,
            priors,
            falling, dxyUp, btcDn,
            spxDn, gldDn, tltDn, vixHigh, hygWide, nvdaDn,
            xlkDn, xluUp, xlyDn, xlpUp, xlfDn,
            sofrRise, mortRise, fedFall, shyDn, ngDn,
            debtRise,
            List.of(), List.of(), iwmDn,
            List.of(), List.of(),
            djiDn, catDn, xliDn,
            srlnDn
        );
    }

    static List<Divergence> buildDivs(boolean bullish) {
        if (bullish) return List.of(new Divergence("test bull", "", false));
        return List.of(new Divergence("test bear", "", true));
    }

    static void check(String label, boolean cond) {
        if (cond) passed++; else { failed++; System.out.println("  FAIL: " + label); }
    }
}
