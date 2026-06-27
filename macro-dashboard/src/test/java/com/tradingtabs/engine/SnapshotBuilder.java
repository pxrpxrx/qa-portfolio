package com.tradingtabs.engine;

import java.time.LocalDate;
import java.util.*;

/**
 * Factory for creating test Snapshot instances with configurable values.
 * Uses sensible defaults that can be overridden per test.
 */
public class SnapshotBuilder {

    private LocalDate date = LocalDate.of(2026, 6, 26);
    private double iorb = 3.65;
    private double m2 = 21.5;
    private double tga = 0.92;
    private double onrrp = 0.01;
    private double gdp = 27.0;
    private double baa10y = 1.52;
    private double dgs10 = 4.41;
    private double dgs3mo = 3.85;
    private double dgs2 = 4.11;
    private double deficit = -1.8;
    private double unrate = 4.0;
    private double dxy = 104.5;
    private double spx = 5400;
    private double ndx = 18500;
    private double gld = 235;
    private double tlt = 92;
    private double hyg = 79.5;
    private double nvda = 120;
    private double xlk = 100;
    private double xlu = 70;
    private double xly = 95;
    private double xlp = 80;
    private double xlf = 42;
    private double vix = 18;
    private double sofr = 5.3;
    private double mortgage30 = 6.8;
    private double pce = 130;
    private double t5yie = 2.2;
    private double fedBalance = 7.5;
    private double shy = 97;
    private double icln = 20;
    private double lac = 15;
    private double ita = 130;
    private double arkx = 25;
    private double bx = 140;
    private double blk = 800;
    private double ng = 2.5;
    private double srln = 42;
    private double copper = 38;
    private double oil = 75;
    private double silver = 28;
    private double totalDebt = 34.5;
    private double iwm = 200;
    private double dji = 39000;
    private double cat = 350;
    private double xli = 120;
    private double btcPrice = 65000;
    private double btcFunding = 0.0001;
    private double btcVolume = 30_000_000_000.0;
    private double btcOi = 15_000_000_000.0;
    private Map<String, Double> priors = new HashMap<>();

    // 6 elements so pctChange(history, 5) works (needs size >= lookback + 1)
    private List<Double> m2History = List.of(20.8, 21.0, 21.1, 21.2, 21.3, 21.5);
    private List<Double> dxyHistory = List.of(104.0, 104.1, 104.2, 104.3, 104.4, 104.5);
    private List<Double> btcHistory = List.of(62000.0, 63000.0, 63500.0, 64000.0, 64500.0, 65000.0);
    private List<Double> spxHistory = List.of(5350.0, 5360.0, 5370.0, 5380.0, 5390.0, 5400.0);
    private List<Double> gldHistory = List.of(233.0, 233.5, 234.0, 234.5, 234.8, 235.0);
    private List<Double> tltHistory = List.of(91.0, 91.2, 91.5, 91.8, 91.9, 92.0);
    private List<Double> vixHistory = List.of(17.0, 17.5, 18.0, 18.5, 18.2, 18.0);
    private List<Double> hygHistory = List.of(79.0, 79.1, 79.2, 79.3, 79.4, 79.5);
    private List<Double> nvdaHistory = List.of(118.0, 119.0, 119.5, 120.0, 120.0, 120.0);
    private List<Double> xlkHistory = List.of(99.0, 99.2, 99.5, 99.8, 99.9, 100.0);
    private List<Double> xluHistory = List.of(69.0, 69.2, 69.5, 69.8, 69.9, 70.0);
    private List<Double> xlyHistory = List.of(94.0, 94.2, 94.5, 94.8, 94.9, 95.0);
    private List<Double> xlpHistory = List.of(79.5, 79.6, 79.7, 79.8, 79.9, 80.0);
    private List<Double> xlfHistory = List.of(41.5, 41.6, 41.7, 41.8, 41.9, 42.0);
    private List<Double> sofrHistory = List.of(5.28, 5.29, 5.30, 5.30, 5.30, 5.30);
    private List<Double> mortgage30History = List.of(6.7, 6.75, 6.78, 6.80, 6.80, 6.80);
    private List<Double> fedBalanceHistory = List.of(7.4, 7.42, 7.45, 7.48, 7.49, 7.5);
    private List<Double> shyHistory = List.of(96.8, 96.9, 96.95, 97.0, 97.0, 97.0);
    private List<Double> ngHistory = List.of(2.3, 2.35, 2.4, 2.45, 2.48, 2.5);
    private List<Double> totalDebtHistory = List.of(34.0, 34.1, 34.2, 34.3, 34.4, 34.5);
    private List<Double> dgs2History = List.of(4.0, 4.02, 4.05, 4.08, 4.10, 4.11);
    private List<Double> t5yieHistory = List.of(2.1, 2.12, 2.15, 2.18, 2.19, 2.2);
    private List<Double> iwmHistory = List.of(198.0, 198.5, 199.0, 199.5, 199.8, 200.0);
    private List<Double> ndxHistory = List.of(18300.0, 18350.0, 18400.0, 18450.0, 18480.0, 18500.0);
    private List<Double> copperHistory = List.of(37.0, 37.2, 37.5, 37.8, 37.9, 38.0);
    private List<Double> djiHistory = List.of(38800.0, 38850.0, 38900.0, 38950.0, 38980.0, 39000.0);
    private List<Double> catHistory = List.of(345.0, 346.0, 347.0, 348.0, 349.0, 350.0);
    private List<Double> xliHistory = List.of(119.0, 119.2, 119.5, 119.8, 119.9, 120.0);
    private List<Double> srlnHistory = List.of(41.5, 41.7, 41.8, 42.0, 42.0, 42.0);

    public SnapshotBuilder withBtcPrice(double price) { this.btcPrice = price; return this; }
    public SnapshotBuilder withBtcFunding(double funding) { this.btcFunding = funding; return this; }
    public SnapshotBuilder withBtcVolume(double vol) { this.btcVolume = vol; return this; }
    public SnapshotBuilder withBtcOi(double oi) { this.btcOi = oi; return this; }
    public SnapshotBuilder withBtcHistory(List<Double> hist) { this.btcHistory = hist; return this; }
    public SnapshotBuilder withM2(double m2) { this.m2 = m2; return this; }
    public SnapshotBuilder withM2History(List<Double> hist) { this.m2History = hist; return this; }
    public SnapshotBuilder withTga(double tga) { this.tga = tga; return this; }
    public SnapshotBuilder withOnrrp(double onrrp) { this.onrrp = onrrp; return this; }
    public SnapshotBuilder withDgs10(double dgs10) { this.dgs10 = dgs10; return this; }
    public SnapshotBuilder withDgs3mo(double dgs3mo) { this.dgs3mo = dgs3mo; return this; }
    public SnapshotBuilder withBaa10y(double baa10y) { this.baa10y = baa10y; return this; }
    public SnapshotBuilder withDxy(double dxy) { this.dxy = dxy; return this; }
    public SnapshotBuilder withDxyHistory(List<Double> hist) { this.dxyHistory = hist; return this; }
    public SnapshotBuilder withVix(double vix) { this.vix = vix; return this; }

    public DataManager.Snapshot build() {
        return new DataManager.Snapshot(
            date, iorb, m2, tga, onrrp, gdp, baa10y, dgs10, dgs3mo, dgs2,
            deficit, unrate, dxy, spx, ndx, gld, tlt, hyg, nvda,
            xlk, xlu, xly, xlp, xlf, vix, sofr, mortgage30, pce, t5yie, fedBalance,
            shy, icln, lac, ita, arkx, bx, blk, ng, srln,
            copper, oil, silver, totalDebt, iwm, dji, cat, xli,
            btcPrice, btcFunding, btcVolume, btcOi,
            priors,
            m2History, dxyHistory, btcHistory,
            spxHistory, gldHistory, tltHistory, vixHistory, hygHistory, nvdaHistory,
            xlkHistory, xluHistory, xlyHistory, xlpHistory, xlfHistory,
            sofrHistory, mortgage30History, fedBalanceHistory, shyHistory, ngHistory,
            totalDebtHistory, dgs2History, t5yieHistory, iwmHistory,
            ndxHistory, copperHistory, djiHistory, catHistory, xliHistory, srlnHistory
        );
    }
}
