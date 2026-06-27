package com.tradingtabs.horizon;

import com.tradingtabs.engine.*;
import com.tradingtabs.engine.MacroContext.MacroResult;
import com.tradingtabs.engine.BtcFrame.BtcResult;
import com.tradingtabs.engine.DivergenceScanner.Divergence;
import java.time.LocalDate;
import java.util.*;

public class HorizonMatrix {

    public record MetricRow(String label, String current, String prior, String unit, String dir, String horizon, String note, String pair, String ref) {}

    private MetricRow mr(String label, String cur, String prior, String unit, String dir, String hor, String note) {
        return new MetricRow(label, cur, prior, unit, dir, hor, note, "", "");
    }
    public record HorizonView(String status, String emoji, List<String> factors, String summary) {}
    public record Scenario(String name, String emoji, double prob, String priceRange, String trigger, String narrative) {}

    public record MicroSection(
        double vix, double vixTrend,
        double goldTrend, double copper,
        Map<String,Double> sector5d,
        String riskRegime, String sectorSignal,
        double bankPoverty, double mbsSpread, double mortgageRate,
        double pce, double qeQt,
        double natGasTrend, double shyTrend,
        Map<String,Double> frameworkPrices
    ) {}

    public record HorizonResult(
        LocalDate date, double btcPrice, double fairValue,
        List<MetricRow> metrics,
        HorizonView shortTerm, HorizonView mediumTerm, HorizonView longTerm,
        MicroSection micro,
        List<Scenario> scenarios,
        List<String> divergences, String macroStatus, String btcStatus,
        List<MetricRow> frameworkRows
    ) {}

    public HorizonResult analyze(DataManager.Snapshot snap, MacroResult macro, BtcResult btc, List<Divergence> divs) {
        double p = snap.btcPrice();
        double ma = btc != null ? btc.fairValue() : p;
        double momentum = btc != null ? btc.momentum() : 0;

        List<MetricRow> metrics = buildMetrics(snap, macro, btc);
        MicroSection micro = buildMicro(snap);
        List<MetricRow> fwRows = buildFrameworkRows(snap, micro.frameworkPrices());
        HorizonView st = assessShortTerm(snap, macro, btc, momentum, p, ma, micro);
        HorizonView mt = assessMediumTerm(snap, macro, btc, divs, p, ma, micro);
        HorizonView lt = assessLongTerm(snap, macro, btc, p, ma);
        List<Scenario> scens = buildScenarios(st, mt, lt, btc, p, ma);
        List<String> divLabels = divs.stream().map(d -> d.label() + (d.bearish() ? " BEAR" : "")).toList();

        return new HorizonResult(
            snap.date(), p, ma, metrics, st, mt, lt, micro, scens,
            divLabels,
            macro != null ? macro.status() : "-",
            btc != null ? btc.status() : "-",
            fwRows
        );
    }

    // -- METRIC TABLE (grouped, with proper priors) -----------------------
    private List<MetricRow> buildMetrics(DataManager.Snapshot snap, MacroResult macro, BtcResult btc) {
        List<MetricRow> rows = new ArrayList<>();
        Map<String,Double> p = snap.priors();
        double p_btc = snap.btcPrice();
        double ma = btc != null ? btc.fairValue() : p_btc;
        double nPrior;

        // ── LIQUIDITY ──
        rows.add(groupHeader("LIQUIDITY"));
        double iorbP = p.getOrDefault("iorb", Double.NaN);
        if (!Double.isNaN(snap.iorb()) && !Double.isNaN(iorbP))
            rows.add(formatVal("IORB", snap.iorb(), iorbP, "%", false, "1-3m",
                snap.iorb() > 5.5 ? "tight" : snap.iorb() < 4.0 ? "easing" : "neutral"));
        double tgaP = p.getOrDefault("tga", Double.NaN);
        if (!Double.isNaN(snap.tga()) && !Double.isNaN(tgaP))
            rows.add(formatVal("TGA", snap.tga(), tgaP, "T", true, "1-3m",
                snap.tga() > 0.5 ? "high" : snap.tga() < 0.1 ? "low" : "normal"));
        double onrrpP = p.getOrDefault("onrrp", Double.NaN);
        if (!Double.isNaN(snap.onrrp()) && !Double.isNaN(onrrpP))
            rows.add(formatVal("ON RRP", snap.onrrp(), onrrpP, "T", true, "1-3m",
                snap.onrrp() > 0.1 ? "draining" : "drained"));
        if (macro != null) {
            rows.add(formatVal("Net liquidity", macro.netLiquidity(), 0.0, "T", true, "6-12m", ""));
            nPrior = calcPrior(snap.m2History(), 1);
            rows.add(formatPct("M2 momentum", macro.m2Momentum(), nPrior, true, "3-12m", "liquidity"));
        }
        if (!Double.isNaN(snap.fedBalance()) && snap.fedBalance() > 0) {
            nPrior = calcPrior(snap.fedBalanceHistory(), 1);
            rows.add(formatPct("QE/QT", nPrior, 0.0, true, "1-3m",
                nPrior > 0.002 ? "QE" : nPrior < -0.002 ? "QT" : "neutral"));
        }

        // ── YIELDS ──
        rows.add(groupHeader("YIELDS"));
        if (macro != null) {
            double dgs10P = p.getOrDefault("dgs10", Double.NaN);
            double dgs3moP = p.getOrDefault("dgs3mo", Double.NaN);
            double tsPrior = (!Double.isNaN(dgs10P) && !Double.isNaN(dgs3moP))
                ? dgs10P - dgs3moP : macro.termSpread() - 0.1;
            rows.add(formatVal("Term spread", macro.termSpread(), tsPrior, "pp", false, "6-12m",
                macro.termSpread() > 0 ? "curve normal" : "inverted"));
        }
        double dgs10P = p.getOrDefault("dgs10", Double.NaN);
        if (!Double.isNaN(snap.dgs10()) && !Double.isNaN(dgs10P))
            rows.add(formatVal("DGS10", snap.dgs10(), dgs10P, "%", false, "1-6m",
                snap.dgs10() > 4.5 ? "high" : snap.dgs10() < 3.0 ? "low" : "neutral"));
        double dgs3moP = p.getOrDefault("dgs3mo", Double.NaN);
        if (!Double.isNaN(snap.dgs3mo()) && !Double.isNaN(dgs3moP))
            rows.add(formatVal("DGS3MO", snap.dgs3mo(), dgs3moP, "%", false, "1-3m",
                snap.dgs3mo() > 5.0 ? "tight" : snap.dgs3mo() < 3.0 ? "loose" : "neutral"));
        double dgs2P = p.getOrDefault("dgs2", Double.NaN);
        if (!Double.isNaN(snap.dgs2()) && !Double.isNaN(dgs2P))
            rows.add(formatVal("DGS2", snap.dgs2(), dgs2P, "%", false, "1-6m",
                snap.dgs2() > 5.0 ? "front end tight" : snap.dgs2() < 3.0 ? "front end loose" : ""));
        double baaP = p.getOrDefault("baa10y", Double.NaN);
        if (!Double.isNaN(snap.baa10y()) && !Double.isNaN(baaP))
            rows.add(formatVal("BAA-10Y spr", snap.baa10y(), baaP, "pp", false, "1-6m",
                snap.baa10y() > 3.0 ? "credit stress" : snap.baa10y() < 1.5 ? "credit easy" : "normal"));
        if (macro != null) {
            double hygPrior = macro.hygSpread() > 3 ? macro.hygSpread() - 0.5 : macro.hygSpread() + 0.3;
            rows.add(formatVal("HYG spread", macro.hygSpread(), hygPrior, "%", false, "1-3m",
                macro.hygSpread() < 3 ? "risk-on" : macro.hygSpread() > 5 ? "credit stress" : "normal"));
        }
        if (!Double.isNaN(snap.mortgage30()) && !Double.isNaN(snap.dgs10())) {
            double mbsSpr = snap.mortgage30() - snap.dgs10();
            double mortP = p.getOrDefault("mortgage30", snap.mortgage30() - 0.2);
            rows.add(formatVal("Mortgage30", snap.mortgage30(), mortP, "%", false, "1-6m",
                snap.mortgage30() > 7 ? "housing stress" : snap.mortgage30() < 5 ? "refi zone" : ""));
            rows.add(formatVal("MBS spread", mbsSpr, 0.0, "pp", false, "1-6m",
                mbsSpr > 3 ? "Burry signal" : "normal"));
        }

        // ── SECTORS ──
        rows.add(groupHeader("SECTORS"));
        double xlkMom = calcPrior(snap.xlkHistory(), 5);
        double xluMom = calcPrior(snap.xluHistory(), 5);
        double xlyMom = calcPrior(snap.xlyHistory(), 5);
        double xlpMom = calcPrior(snap.xlpHistory(), 5);
        double xlfMom = calcPrior(snap.xlfHistory(), 5);
        if (!Double.isNaN(xlkMom) && xlkMom != 0)
            rows.add(formatPct("XLK", xlkMom, 0.0, true, "1-3m", xlkMom > xluMom ? "leading" : "lagging"));
        if (!Double.isNaN(xluMom) && xluMom != 0)
            rows.add(formatPct("XLU", xluMom, 0.0, false, "1-3m", xluMom > xlkMom ? "defensive rotation" : ""));
        if (!Double.isNaN(xlyMom) && xlyMom != 0)
            rows.add(formatPct("XLY", xlyMom, 0.0, true, "1-3m", xlyMom > xlpMom ? "consumer strong" : "consumer weak"));
        if (!Double.isNaN(xlpMom) && xlpMom != 0)
            rows.add(formatPct("XLP", xlpMom, 0.0, false, "1-3m", ""));
        if (!Double.isNaN(xlfMom) && xlfMom != 0)
            rows.add(formatPct("XLF", xlfMom, 0.0, true, "1-3m", xlfMom > 0 ? "credit easing" : "credit tightening"));

        // ── COMMODITIES ──
        rows.add(groupHeader("COMMODITIES"));
        rows.add(formatVal("GLD ETF", snap.gld(), calcPrior(snap.gldHistory(), 5), "USD", false, "3-12m",
            snap.gld() > 250 ? "ATH territory" : ""));
        double copperP = p.getOrDefault("copper", Double.NaN);
        if (!Double.isNaN(snap.copper()) && !Double.isNaN(copperP))
            rows.add(formatVal("Copper (CPER)", snap.copper(), copperP, "USD", true, "1-6m",
                snap.copper() > 40 ? "infra demand" : snap.copper() < 30 ? "demand fear" : ""));
        double oilP = p.getOrDefault("oil", Double.NaN);
        if (!Double.isNaN(snap.oil()) && !Double.isNaN(oilP))
            rows.add(formatVal("Oil (USO)", snap.oil(), oilP, "USD", false, "1-6m",
                snap.oil() > 75 ? "energy costly" : snap.oil() < 55 ? "demand fear" : ""));
        double silverP = p.getOrDefault("silver", Double.NaN);
        if (!Double.isNaN(snap.silver()) && !Double.isNaN(silverP))
            rows.add(formatVal("Silver (SLV)", snap.silver(), silverP, "USD", false, "1-6m",
                snap.silver() > 30 ? "monetary demand" : ""));
        double ngMom = calcPrior(snap.ngHistory(), 5);
        if (!Double.isNaN(ngMom) && ngMom != 0)
            rows.add(formatPct("Nat gas", ngMom, 0.0, false, "1-3m",
                ngMom > 0.03 ? "energy spike" : ngMom < -0.03 ? "energy dump" : ""));

        // ── MACRO ──
        rows.add(groupHeader("MACRO"));
        if (macro != null) {
            rows.add(formatPct("DXY trend", macro.dxyTrend(), 0.0, false, "1-3m",
                macro.dxyTrend() < -0.005 ? "weakens" : macro.dxyTrend() > 0.005 ? "strengthens" : "stable"));
        }
        double pceP = p.getOrDefault("pce", Double.NaN);
        if (!Double.isNaN(snap.pce()) && !Double.isNaN(pceP))
            rows.add(formatVal("PCE index", snap.pce(), pceP, "", false, "6-12m",
                snap.pce() > 130 ? "sticky" : snap.pce() < 125 ? "cooling" : "stable"));
        double t5yieP = p.getOrDefault("t5yie", Double.NaN);
        if (!Double.isNaN(snap.t5yie()) && !Double.isNaN(t5yieP))
            rows.add(formatVal("5Y BE", snap.t5yie(), t5yieP, "%", false, "3-6m",
                snap.t5yie() > 2.8 ? "inflation concern" : snap.t5yie() < 2.0 ? "disinflation" : "normal"));
        double vixLevel = snap.vix();
        if (!Double.isNaN(vixLevel) && vixLevel > 0) {
            double vix5d = calcPrior(snap.vixHistory(), 5);
            rows.add(formatVal("VIX", vixLevel, vixLevel + vix5d * 20, "", false, "1-2w",
                vixLevel > 30 ? "panic" : vixLevel > 20 ? "fear" : vixLevel < 13 ? "complacent" : "normal"));
        }
        double spxMom = calcPrior(snap.spxHistory(), 5);
        if (!Double.isNaN(spxMom) && spxMom != 0)
            rows.add(formatPct("SPX momentum", spxMom, 0.0, true, "1-3m",
                spxMom > 0.02 ? "risk-on" : spxMom < -0.02 ? "risk-off" : "flat"));
        double tltMom = calcPrior(snap.tltHistory(), 5);
        if (!Double.isNaN(tltMom) && tltMom != 0)
            rows.add(formatPct("TLT momentum", tltMom, 0.0, true, "1-3m",
                tltMom > 0.01 ? "rates down" : tltMom < -0.01 ? "rates up" : "flat"));
        // IWM small caps
        double iwmMom = calcPrior(snap.iwmHistory(), 5);
        if (!Double.isNaN(iwmMom) && iwmMom != 0)
            rows.add(formatPct("IWM small caps", iwmMom, 0.0, true, "1-3m",
                iwmMom > 0.02 ? "risk-on" : iwmMom < -0.02 ? "risk-off" : ""));
        double shyMom = calcPrior(snap.shyHistory(), 5);
        if (!Double.isNaN(shyMom) && shyMom != 0)
            rows.add(formatPct("SHY short Tsy", shyMom, 0.0, true, "1-3m",
                shyMom > 0 ? "front end bid" : "front end sell"));

        // ── BTC ──
        rows.add(groupHeader("BTC"));
        if (btc != null) {
            double momPrior = calcPrior(snap.btcHistory(), 5);
            rows.add(formatPct("Momentum", btc.momentum(), momPrior, true, "1-2w",
                btc.momentum() > 0.02 ? "rally" : btc.momentum() < -0.02 ? "selloff" : "flat"));
            rows.add(formatPct("Funding rate", snap.btcFunding(), 0.0, false, "1w",
                snap.btcFunding() > 0.0001 ? "overheated" : snap.btcFunding() < -0.0001 ? "shorts pay" : "neutral"));
            double pctFromMa = ma > 0 ? (p_btc / ma - 1) * 100 : 0;
            rows.add(formatVal("vs MA200", pctFromMa, 0.0, "%", true, "1-3m",
                pctFromMa < -5 ? "extreme below" : pctFromMa > 5 ? "extreme above" : "near MA"));
        }

        // ── FISCAL ──
        rows.add(groupHeader("FISCAL"));
        double deficitP = p.getOrDefault("deficit", Double.NaN);
        if (!Double.isNaN(snap.deficit()) && !Double.isNaN(deficitP))
            rows.add(formatVal("Deficit (FY)", snap.deficit(), deficitP, "T", false, "12m",
                snap.deficit() < -1.0 ? "fiscal drag" : snap.deficit() < -0.5 ? "moderate" : "improving"));
        if (!Double.isNaN(snap.totalDebt())) {
            double tdPrior = calcPrior(snap.totalDebtHistory(), 1);
            rows.add(formatVal("Total debt", snap.totalDebt(), tdPrior > 0 ? tdPrior : 0.0, "T", false, "12m",
                snap.totalDebt() > 33 ? "record high" : ""));
            double debtGdp = !Double.isNaN(snap.gdp()) && snap.gdp() > 0 ? (snap.totalDebt() / snap.gdp()) * 100 : 0;
            if (debtGdp > 0)
                rows.add(formatVal("Debt/GDP", debtGdp, 0.0, "%", false, "12m",
                    debtGdp > 120 ? "unsustainable" : debtGdp > 100 ? "elevated" : "normal"));
        }
        String gapNote = !Double.isNaN(snap.deficit())
            ? String.format("act $%.1fT vs req $7.3T vs CBO $6.9T", -snap.deficit()) : "";
        rows.add(mr("Budget gap", "see note", "", "", "", "FY26", gapNote));

        return rows;
    }

    private MetricRow groupHeader(String name) {
        return mr("--- " + name + " ---", "", "", "", "", "", "");
    }

    // -- MICRO SECTION -------------------------------------------------
    private MicroSection buildMicro(DataManager.Snapshot snap) {
        double vix = snap.vix();
        double vix5d = calcPrior(snap.vixHistory(), 5);
        double gldMom = calcPrior(snap.gldHistory(), 5);
        double spxMom = calcPrior(snap.spxHistory(), 5);

        double xlk5d = calcPrior(snap.xlkHistory(), 5);
        double xlu5d = calcPrior(snap.xluHistory(), 5);
        double xly5d = calcPrior(snap.xlyHistory(), 5);
        double xlp5d = calcPrior(snap.xlpHistory(), 5);
        double xlf5d = calcPrior(snap.xlfHistory(), 5);

        Map<String,Double> sector5d = new LinkedHashMap<>();
        sector5d.put("XLK", xlk5d); sector5d.put("XLU", xlu5d);
        sector5d.put("XLY", xly5d); sector5d.put("XLP", xlp5d); sector5d.put("XLF", xlf5d);

        // Risk regime
        String riskRegime;
        if (vix > 30) riskRegime = "PANIC";
        else if (vix > 20) riskRegime = "VOLATILE";
        else if (vix < 13) riskRegime = "COMPLACENT";
        else riskRegime = "NORMAL";

        // Sector rotation signal
        String sectorSignal;
        double avgDef = (xlu5d + xlp5d) / 2;
        if (xlk5d > avgDef + 0.01) sectorSignal = "TECH LEADS";
        else if (xlu5d > xlk5d + 0.005) sectorSignal = "DEFENSIVE ROTATION";
        else if (xly5d > xlp5d + 0.01) sectorSignal = "CONSUMER STRONG";
        else if (xlp5d > xly5d + 0.01) sectorSignal = "CONSUMER WEAK";
        else sectorSignal = "NO CLEAR LEADERSHIP";

        // New computed metrics
        double bankPoverty = (!Double.isNaN(snap.sofr()) && !Double.isNaN(snap.iorb()))
            ? snap.sofr() - snap.iorb() : Double.NaN;
        double mbsSpread = (!Double.isNaN(snap.mortgage30()) && !Double.isNaN(snap.dgs10()))
            ? snap.mortgage30() - snap.dgs10() : Double.NaN;
        double qeQt = calcPrior(snap.fedBalanceHistory(), 1);
        double ngMom = calcPrior(snap.ngHistory(), 5);
        double shyMom = calcPrior(snap.shyHistory(), 5);

        // Framework prices: flat map of all tickers the user tracks
        Map<String,Double> fw = new LinkedHashMap<>();
        fw.put("NVDA", snap.nvda()); fw.put("XLK", snap.xlk());
        fw.put("XLY", snap.xly()); fw.put("XLP", snap.xlp());
        fw.put("XLU", snap.xlu()); fw.put("XLF", snap.xlf());
        fw.put("DXY", snap.dxy());
        fw.put("TLT", snap.tlt());
        fw.put("XAU", snap.gld()); fw.put("HG1", snap.copper());
        if (!Double.isNaN(snap.srln())) fw.put("SRLN", snap.srln());
        fw.put("SHY", snap.shy()); fw.put("HYG", snap.hyg());
        fw.put("NG", snap.ng());
        fw.put("SPX", snap.spx()); fw.put("QQQ", snap.ndx());
        fw.put("VIX", snap.vix()); fw.put("BTC", snap.btcPrice());
        fw.put("NASD", snap.ndx()); fw.put("ICLN", snap.icln());
        fw.put("LAC", snap.lac()); fw.put("ITA", snap.ita());
        fw.put("ARKX", snap.arkx()); fw.put("BX", snap.bx());
        fw.put("BLK", snap.blk());
        if (!Double.isNaN(snap.mortgage30())) fw.put("MORTG", snap.mortgage30());
        fw.put("IORB", snap.iorb()); fw.put("SOFR", snap.sofr());
        fw.put("MBS", mbsSpread); fw.put("PCE", snap.pce());
        fw.put("FEDBAL", snap.fedBalance());
        fw.put("UNRATE", snap.unrate());
        fw.put("COPPER", snap.copper()); fw.put("OIL", snap.oil());
        fw.put("SILVER", snap.silver()); fw.put("TOTALDEBT", snap.totalDebt());
        fw.put("DEFICIT", snap.deficit()); fw.put("GDP", snap.gdp());
        if (!Double.isNaN(snap.dji())) fw.put("DJI", snap.dji());
        if (!Double.isNaN(snap.cat())) fw.put("CAT", snap.cat());
        if (!Double.isNaN(snap.xli())) fw.put("XLI", snap.xli());

        return new MicroSection(vix, vix5d, gldMom, snap.gld(), sector5d,
            riskRegime, sectorSignal,
            bankPoverty, mbsSpread, snap.mortgage30(),
            snap.pce(), qeQt,
            ngMom, shyMom, fw);
    }

    // -- SHORT-TERM (1-2w) -----------------------------------------------
    private HorizonView assessShortTerm(DataManager.Snapshot snap, MacroResult macro, BtcResult btc,
                                        double momentum, double price, double ma, MicroSection micro) {
        List<String> factors = new ArrayList<>();
        int bull = 0, bear = 0;

        if (momentum > 0.02) { bull++; factors.add("BTC momentum +" + fmtPct(momentum)); }
        else if (momentum < -0.02) { bear++; factors.add("BTC momentum " + fmtPct(momentum) + " down"); }
        else factors.add("BTC momentum neutral");

        double fr = snap.btcFunding();
        if (fr > 0 && fr < 0.01) { bull++; factors.add("funding " + fmtFr(fr)); }
        else if (fr < 0) { bear++; factors.add("funding " + fmtFr(fr) + " bear"); }
        else factors.add("funding neutral");

        double dist = ma > 0 ? (price / ma - 1) * 100 : 0;
        if (dist > -5) { bull++; factors.add("BTC " + fmtDist(dist) + " from MA"); }
        else if (dist < -8) { bear++; factors.add("BTC " + fmtDist(dist) + " deep below MA"); }
        else factors.add("BTC " + fmtDist(dist) + " from MA");

        double volOi = snap.btcVolume() / snap.btcOi();
        if (!Double.isNaN(volOi) && volOi > 0.04 && volOi < 100) { bull++; factors.add("volume/OI " + String.format("%.1fx", volOi)); }

        // VIX short-term factor
        if (micro != null && micro.vix() > 25) { bear++; factors.add("VIX " + String.format("%.1f", micro.vix()) + " elevated"); }
        else if (micro != null && micro.vix() < 14) { bull++; factors.add("VIX " + String.format("%.1f", micro.vix()) + " low"); }

        String status, emoji;
        if (bull >= 3 && bear <= 1) { status = "BULLISH"; emoji = "GREEN"; }
        else if (bear >= 2 && bull <= 1) { status = "BEARISH"; emoji = "RED"; }
        else if (bull >= 2 && bear >= 2) { status = "MIXED"; emoji = "YELLOW"; }
        else { status = "NEUTRAL"; emoji = "GRAY"; }

        String summary;
        if (status.equals("BULLISH")) summary = "Positive momentum, healthy funding, low VIX";
        else if (status.equals("BEARISH")) summary = "Negative momentum, below MA, VIX elevated";
        else summary = "Mixed signals, no clear catalyst";

        return new HorizonView(status, emoji, factors, summary);
    }

    // -- MEDIUM-TERM (1-3m) ----------------------------------------------
    private HorizonView assessMediumTerm(DataManager.Snapshot snap, MacroResult macro, BtcResult btc,
                                         List<Divergence> divs, double price, double ma, MicroSection micro) {
        List<String> factors = new ArrayList<>();
        int bull = 0, bear = 0;

        if (macro != null) {
            if (macro.hygSpread() < 3.0) { bull++; factors.add("HYG " + String.format("%.1f", macro.hygSpread()) + "% risk-on"); }
            else if (macro.hygSpread() > 5.0) { bear++; factors.add("HYG " + String.format("%.1f", macro.hygSpread()) + "% stress"); }
            else factors.add("HYG " + String.format("%.1f", macro.hygSpread()) + "% normal");

            if (macro.dxyTrend() < -0.005) { bull++; factors.add("DXY " + fmtPct(macro.dxyTrend()) + " weak"); }
            else if (macro.dxyTrend() > 0.005) { bear++; factors.add("DXY " + fmtPct(macro.dxyTrend()) + " strong"); }
            else factors.add("DXY stable");
        }

        long bullishDivs = divs.stream().filter(d -> !d.bearish()).count();
        long bearishDivs = divs.stream().filter(Divergence::bearish).count();
        if (bullishDivs > bearishDivs) { bull++; factors.add("divergence bullish"); }
        else if (bearishDivs > bullishDivs) { bear++; factors.add("divergence bearish"); }

        double dist = ma > 0 ? (price / ma - 1) * 100 : 0;
        if (dist < -10) { bull++; factors.add("BTC oversold mean-reversion"); }

        // Medium-term micro factors
        if (micro != null) {
            if (micro.goldTrend() > 0.02) { bull++; factors.add("gold bid " + fmtPct(micro.goldTrend())); }
            if (micro.sectorSignal().contains("TECH LEADS") || micro.sectorSignal().contains("CONSUMER STRONG")) {
                bull++; factors.add(micro.sectorSignal());
            }
            if (micro.sectorSignal().contains("DEFENSIVE") || micro.sectorSignal().contains("CONSUMER WEAK")) {
                bear++; factors.add(micro.sectorSignal());
            }
        }

        String status, emoji;
        if (bull >= 3 && bear <= 1) { status = "BULLISH"; emoji = "GREEN"; }
        else if (bear >= 3 && bull <= 1) { status = "BEARISH"; emoji = "RED"; }
        else if (bull >= 2 && bear >= 2) { status = "MIXED"; emoji = "YELLOW"; }
        else { status = "NEUTRAL"; emoji = "GRAY"; }

        String summary;
        if (status.equals("BULLISH")) summary = "Macro + micro support: HYG tight, weak dollar, bull divergences";
        else if (status.equals("BEARISH")) summary = "Macro + micro pressure: credit stress, dollar strong, defensive rotation";
        else summary = "Mixed macro/micro signals";

        return new HorizonView(status, emoji, factors, summary);
    }

    // -- LONG-TERM (3-12m) -----------------------------------------------
    private HorizonView assessLongTerm(DataManager.Snapshot snap, MacroResult macro, BtcResult btc,
                                       double price, double ma) {
        List<String> factors = new ArrayList<>();
        int bull = 0, bear = 0;

        if (macro != null) {
            if (macro.m2Momentum() > 0.002) { bull++; factors.add("M2 " + fmtPct(macro.m2Momentum()) + " growing"); }
            else if (macro.m2Momentum() < -0.002) { bear++; factors.add("M2 " + fmtPct(macro.m2Momentum()) + " shrinking"); }

            if (macro.termSpread() > 0) { bull++; factors.add("term " + String.format("%+.2f", macro.termSpread()) + " normal"); }
            else if (macro.termSpread() < -0.5) { bear++; factors.add("term " + String.format("%.1f", macro.termSpread()) + " inverted"); }

            if (macro.netLiquidity() > 20.0) { bull++; factors.add("net liq " + String.format("%.1fT", macro.netLiquidity())); }
            else if (macro.netLiquidity() < 18.0) { bear++; factors.add("net liq " + String.format("%.1fT", macro.netLiquidity()) + " low"); }

            if (macro.status().equals("GREEN")) bull++;
            else if (macro.status().equals("RED")) bear++;
        }

        // TLT long-term factor
        double tltMom = calcPrior(snap.tltHistory(), 5);
        if (!Double.isNaN(tltMom) && tltMom > 0.01) { bull++; factors.add("TLT up, rates declining"); }
        else if (!Double.isNaN(tltMom) && tltMom < -0.01) { bear++; factors.add("TLT down, rates rising"); }

        // Gold as macro hedge
        double gldMom = calcPrior(snap.gldHistory(), 5);
        if (!Double.isNaN(gldMom) && gldMom > 0.02) { bull++; factors.add("gold bid " + fmtPct(gldMom) + " macro hedge"); }

        String status, emoji;
        if (bull >= 3 && bear <= 1) { status = "BULLISH"; emoji = "GREEN"; }
        else if (bear >= 3 && bull <= 1) { status = "BEARISH"; emoji = "RED"; }
        else if (bull >= 2 && bear >= 2) { status = "MIXED"; emoji = "YELLOW"; }
        else { status = "NEUTRAL"; emoji = "GRAY"; }

        String summary;
        if (status.equals("BULLISH")) summary = "Structural tailwind: M2 growing, curve normal, high liquidity, rates declining";
        else if (status.equals("BEARISH")) summary = "Structural headwind: M2 shrinking, curve inverted, liquidity low, rates rising";
        else summary = "Mixed structural signals";

        return new HorizonView(status, emoji, factors, summary);
    }

    // -- SCENARIOS -------------------------------------------------------
    private List<Scenario> buildScenarios(HorizonView st, HorizonView mt, HorizonView lt, BtcResult btc,
                                         double price, double ma) {
        List<Scenario> scens = new ArrayList<>();
        double s2 = btc != null ? btc.support2() : price * 0.95;
        double r2 = btc != null ? btc.resistance2() : price * 1.05;
        double s1 = btc != null ? btc.support1() : price * 0.97;
        double r1 = btc != null ? btc.resistance1() : price * 1.03;

        boolean bullishBias = st.status().contains("BULL") || mt.status().contains("BULL") || lt.status().contains("BULL");
        boolean bearishBias = st.status().contains("BEAR") || mt.status().contains("BEAR") || lt.status().contains("BEAR");

        double bearProb = bearishBias ? 0.30 : 0.20;
        double bullProb = bullishBias ? 0.30 : 0.20;

        String bearRange = String.format("$%,.0f-%,.0f", s2 * 0.98, s1);
        String baseRange = String.format("$%,.0f-%,.0f", s1, ma * 1.02);
        String bullRange = String.format("$%,.0f-%,.0f", r1, r2 * 1.02);

        scens.add(new Scenario("Bear case", "RED", bearProb, bearRange,
            "ETF outflows persist, BTC loses S1",
            "Continued selling, no reversal catalyst"));

        scens.add(new Scenario("Base case", "GRAY", 0.45, baseRange,
            "Outflows taper, macro stable",
            "Consolidation with gradual recovery toward MA"));

        scens.add(new Scenario("Bull case", "GREEN", bullProb, bullRange,
            "3+ days net ETF inflows, BTC reclaims MA",
            "Catalyst-driven recovery, liquidity returns"));

        return scens;
    }

    // -- HELPERS ---------------------------------------------------------
    private double calcPrior(List<Double> hist, int lookback) {
        return DataManager.pctChange(hist, lookback);
    }

    private MetricRow formatPct(String label, double current, double prior, boolean upIsGood,
                                String horizon, String note) {
        String curStr = String.format("%+.2f%%", current * 100);
        String priorStr = String.format("%+.2f%%", prior * 100);
        String dir = fmtDir(current, prior, upIsGood);
        return mr(label, curStr, priorStr, "%", dir, horizon, note);
    }

    private MetricRow formatVal(String label, double current, double prior, String unit, boolean upIsGood,
                                String horizon, String note) {
        String curStr = String.format("%.2f", current);
        String priorStr = String.format("%.2f", prior);
        String dir = fmtDir(current, prior, upIsGood);
        return mr(label, curStr, priorStr, unit, dir, horizon, note);
    }

    // ─── FRAMEWORK RATIOS ─────────────────────────────────────────
    private List<MetricRow> buildFrameworkRows(DataManager.Snapshot snap, Map<String,Double> fw) {
        List<MetricRow> rows = new ArrayList<>();
        double baa = snap.baa10y();

        // Helpers
        record Pair(String tk1, String tk2) {}

        @FunctionalInterface interface NoteFn { String apply(double cur, double prior, Map<String,Double> fw); }

        record Cat(String name, Pair[] pairs, boolean upIsGood, String horizon, NoteFn noteFn, String ref) {}
        // Define each category: name, pairs, upIsGood, horizon, classification note function
        Cat[] cats = {
            new Cat("IMPULSE", new Pair[]{new Pair("NVDA","XLK")}, true, "1w",
                (c,p,f) -> ratioNote(c, 2.0, 1.0, "NVDA leads", "NVDA lags"), "1.0~2.0"),
            new Cat("WANT/MUST", new Pair[]{new Pair("XLY","XLP")}, true, "3m",
                (c,p,f) -> ratioNote(c, 1.5, 1.05, "consumer strong", "consumer weak"), "1.05~1.5"),
            new Cat("TECH/UTILITIES", new Pair[]{new Pair("XLK","XLU")}, true, "3m",
                (c,p,f) -> ratioNote(c, 4.0, 3.0, "tech leads", "defensive"), "3.0~4.0"),
            new Cat("FREE MONEY", new Pair[]{new Pair("DXY","XLF")}, false, "1w",
                (c,p,f) -> ratioNote(c, 2.5, 2.0, "strong dollar", "weak dollar"), "2.0~2.5"),
            new Cat("DEBT GROWTH", new Pair[]{new Pair("DXY","TLT")}, false, "3m",
                (c,p,f) -> ratioNote(c, 1.6, 1.2, "dollar up", "dollar down"), "1.2~1.6"),
            new Cat("SAVE/INVEST", new Pair[]{new Pair("XAU","TLT")}, false, "6m",
                (c,p,f) -> ratioNote(c, 5.0, 3.0, "gold bid", "bonds bid"), "3.0~5.0"),
            new Cat("STOP/GO", new Pair[]{new Pair("XAU","HG1")}, false, "6m",
                (c,p,f) -> ratioNote(c, 12.0, 8.0, "risk-off", "risk-on"), "8.0~12.0"),
            new Cat("YIELD CRYSIS", new Pair[]{new Pair("TLT","SHY")}, false, "3m",
                (c,p,f) -> ratioNote(c, 1.2, 1.05, "steep", "flat"), "1.05~1.2"),
            new Cat("VOLATILE", new Pair[]{new Pair("QQQ","VIX")}, true, "1w",
                (c,p,f) -> ratioNote(c, 50, 25, "low vol", "high vol"), "25~50"),
            new Cat("TECHNO BUBBLE", new Pair[]{new Pair("QQQ","TLT")}, true, "6m",
                (c,p,f) -> ratioNote(c, 10.0, 6.0, "risk-on", "risk-off"), "6.0~10.0"),
            new Cat("NATURAL FDBACK", new Pair[]{new Pair("TLT","NG")}, false, "3m",
                (c,p,f) -> ratioNote(c, 30, 20, "growth slow", "growth high"), "20~30"),
            new Cat("MARKET HEALTH", new Pair[]{new Pair("HG1","XAU")}, true, "6m",
                (c,p,f) -> ratioNote(c, 0.15, 0.08, "expansion", "contraction"), "0.08~0.15"),
            new Cat("VELOCITY", new Pair[]{new Pair("NVDA","NG")}, true, "1w",
                (c,p,f) -> ratioNote(c, 80, 40, "AI frenzy", "AI cooling"), "40~80"),
            new Cat("FEAR/GREED2", new Pair[]{new Pair("SPX","TLT")}, true, "3m",
                (c,p,f) -> ratioNote(c, 10, 6, "greed", "fear"), "6~10"),
        };
        // Conditionally add XLI-dependent categories
        double xli = fw.getOrDefault("XLI", Double.NaN);
        boolean hasXli = !Double.isNaN(xli) && xli > 0;
        List<Cat> catList = new ArrayList<>(Arrays.asList(cats));
        if (hasXli) {
            catList.add(new Cat("LIQ FLOWS", new Pair[]{new Pair("XLK","XLI")}, true, "3m",
                (c,p,f) -> ratioNote(c, 1.8, 1.2, "tech flows", "industrial flows"), "1.2~1.8"));
            catList.add(new Cat("DEMAND HEALTH", new Pair[]{new Pair("NG","XLI")}, true, "3m",
                (c,p,f) -> ratioNote(c, 0.03, 0.02, "demand high", "demand low"), "0.02~0.03"));
        }

        for (Cat c : catList) {
            double cur = Double.NaN, prior = Double.NaN;
            boolean hasData = true;
            String pairStr = "";

            if (c.pairs().length == 1) {
                Pair p = c.pairs()[0];
                pairStr = p.tk1() + "/" + p.tk2();
                Double v1 = fw.get(p.tk1()), v2 = fw.get(p.tk2());
                if (v1 == null || v2 == null || Double.isNaN(v1) || Double.isNaN(v2) || v2 == 0) hasData = false;
                else cur = v1 / v2;

                // Prior via history lists
                double p1 = getPrior(snap, p.tk1(), 5);
                double p2 = getPrior(snap, p.tk2(), 5);
                if (!Double.isNaN(p1) && !Double.isNaN(p2) && p2 != 0) prior = p1 / p2;
            }
            if (!hasData) continue;

            String curStr = String.format("%.2f", cur);
            String priorStr = Double.isNaN(prior) ? "----" : String.format("%.2f", prior);
            String dir = Double.isNaN(prior) ? "--" : fmtDir(cur, prior, c.upIsGood());
            String note = c.noteFn().apply(cur, prior, fw);
            if (note.startsWith("needs ")) continue;
            rows.add(new MetricRow(c.name(), curStr, priorStr, "r", dir, c.horizon(), note, pairStr, c.ref()));
        }

        // KONDRATIEV (50) — NASDAQ / DJI
        double dji = fw.containsKey("DJI") ? fw.get("DJI") : Double.NaN;
        if (!Double.isNaN(dji) && dji > 0) {
            double kCur = snap.ndx() / dji;
            double djiPrior = getPrior(snap, "DJI", 5);
            double kPrior = !Double.isNaN(djiPrior) && djiPrior > 0 ? snap.ndx() / djiPrior : Double.NaN;
            String kp = Double.isNaN(kPrior) ? "N/A" : String.format("%.4f", kPrior);
            String kDir = Double.isNaN(kPrior) ? "--" : fmtDir(kCur, kPrior, false);
            rows.add(new MetricRow("KONDRATIEV (50)",
                String.format("%.4f", kCur), kp, "r", kDir, "50y", "tech vs old economy", "NDX/DJI", ""));
        } else {
            rows.add(new MetricRow("KONDRATIEV (50)", "N/A", "N/A", "r", "--", "50y", "needs DJI", "NDX/DJI", ""));
        }

        // KUZNETSOV (25) — CAT / NASDAQ (infrastructure vs tech, ~25y cycle)
        double cat = fw.containsKey("CAT") ? fw.get("CAT") : Double.NaN;
        if (!Double.isNaN(cat) && cat > 0) {
            double kzCur = cat / snap.ndx();
            double catPrior = getPrior(snap, "CAT", 5);
            double kzPrior = !Double.isNaN(catPrior) && catPrior > 0 ? catPrior / snap.ndx() : Double.NaN;
            String kzp = Double.isNaN(kzPrior) ? "N/A" : String.format("%.6f", kzPrior);
            String kzDir = Double.isNaN(kzPrior) ? "--" : fmtDir(kzCur, kzPrior, false);
            rows.add(new MetricRow("KUZNETSOV (25)",
                String.format("%.6f", kzCur), kzp, "r", kzDir, "25y", "infra vs tech", "CAT/NDX", ""));
        } else {
            rows.add(new MetricRow("KUZNETSOV (25)", "N/A", "N/A", "r", "--", "25y", "needs CAT", "CAT/NDX", ""));
        }

        // CREDIT CYCLE — BAA10Y spread conditions
        String cycleNote;
        if (baa < 1.5) cycleNote = "EUPHORIA";
        else if (baa < 2.5) cycleNote = "NORMAL";
        else if (baa < 4.0) cycleNote = "STRESS";
        else cycleNote = "PANIC";
        double baaPrior = snap.priors().getOrDefault("baa10y", Double.NaN);
        String ccPrior = !Double.isNaN(baaPrior) ? String.format("%.2f", baaPrior) : "----";
        String ccDir = !Double.isNaN(baaPrior) ? fmtDir(baa, baaPrior, false) : "--";
        rows.add(new MetricRow("CREDIT CYCLE", String.format("%.2f", baa), ccPrior, "pp", ccDir, "cycle", cycleNote, "BAA10Y", "1.5~4.0"));

        // BOILING POINT — HYG price (credit heat)
        double hyg = fw.getOrDefault("HYG", Double.NaN);
        if (!Double.isNaN(hyg) && hyg > 0) {
            double hygPrior = getPrior(snap, "HYG", 5);
            String hp = Double.isNaN(hygPrior) ? "----" : String.format("%.2f", hygPrior);
            String hDir = Double.isNaN(hygPrior) ? "--" : fmtDir(hyg, hygPrior, true);
            String hNote = hyg > 85 ? "credit strong" : hyg > 75 ? "credit normal" : "credit stress";
            rows.add(new MetricRow("BOILING POINT", String.format("%.2f", hyg), hp, "p", hDir, "3m", hNote, "HYG", "75~85"));
        } else {
            rows.add(new MetricRow("BOILING POINT", "N/A", "N/A", "p", "--", "3m", "needs HYG", "HYG", "75~85"));
        }

        // BANK TUNNEL — SRLN price (lending activity)
        double srln = fw.getOrDefault("SRLN", Double.NaN);
        if (!Double.isNaN(srln) && srln > 0) {
            double srlnPrior = getPrior(snap, "SRLN", 5);
            String sp = Double.isNaN(srlnPrior) ? "----" : String.format("%.2f", srlnPrior);
            String sDir = Double.isNaN(srlnPrior) ? "--" : fmtDir(srln, srlnPrior, true);
            String sNote = srln > 50 ? "lending healthy" : srln > 40 ? "lending normal" : "lending tight";
            rows.add(new MetricRow("BANK TUNNEL", String.format("%.2f", srln), sp, "p", sDir, "1m", sNote, "SRLN", "40~50"));
        } else {
            rows.add(new MetricRow("BANK TUNNEL", "N/A", "N/A", "p", "--", "1m", "needs SRLN", "SRLN", "40~50"));
        }

        return rows;
    }

    private double getPrior(DataManager.Snapshot snap, String tk, int offset) {
        return switch (tk) {
            case "NVDA" -> DataManager.priorValue(snap.nvdaHistory(), offset);
            case "XLK"  -> DataManager.priorValue(snap.xlkHistory(), offset);
            case "XLY"  -> DataManager.priorValue(snap.xlyHistory(), offset);
            case "XLP"  -> DataManager.priorValue(snap.xlpHistory(), offset);
            case "XLU"  -> DataManager.priorValue(snap.xluHistory(), offset);
            case "XLF"  -> DataManager.priorValue(snap.xlfHistory(), offset);
            case "DXY"  -> DataManager.priorValue(snap.dxyHistory(), offset);
            case "TLT"  -> DataManager.priorValue(snap.tltHistory(), offset);
            case "XAU"  -> DataManager.priorValue(snap.gldHistory(), offset);
            case "SHY"  -> DataManager.priorValue(snap.shyHistory(), offset);
            case "HYG"  -> DataManager.priorValue(snap.hygHistory(), offset);
            case "SRLN" -> DataManager.priorValue(snap.srlnHistory(), offset);
            case "QQQ"  -> DataManager.priorValue(snap.ndxHistory(), offset);
            case "VIX"  -> DataManager.priorValue(snap.vixHistory(), offset);
            case "HG1"  -> DataManager.priorValue(snap.copperHistory(), offset);
            case "NG"   -> DataManager.priorValue(snap.ngHistory(), offset);
            case "SPX"  -> DataManager.priorValue(snap.spxHistory(), offset);
            case "XLI"  -> DataManager.priorValue(snap.xliHistory(), offset);
            case "DJI"  -> DataManager.priorValue(snap.djiHistory(), offset);
            case "CAT"  -> DataManager.priorValue(snap.catHistory(), offset);
            default -> Double.NaN;
        };
    }

    private static String ratioNote(double val, double high, double low, String hiNote, String loNote) {
        if (Double.isNaN(val)) return "N/A";
        return val > high ? hiNote : val < low ? loNote : "neutral";
    }

    private static String valNote(double v1, double v2, double hi, double lo, String hiNote, String loNote) {
        if (Double.isNaN(v1) || Double.isNaN(v2)) return "N/A";
        return v1 > hi || v2 > hi ? hiNote : v1 < lo || v2 < lo ? loNote : "normal";
    }

    private String fmtDir(double cur, double prior, boolean upIsGood) {
        double eps = 0.001;
        if (Math.abs(cur - prior) < eps) return "->";
        boolean up = cur > prior;
        boolean good = upIsGood ? up : !up;
        return good ? "UP" : "DOWN";
    }

    private String fmtPct(double v) { return String.format("%+.2f%%", v * 100); }
    private String fmtFr(double v) { return String.format("%+.4f", v); }
    private String fmtDist(double v) { return String.format("%+.1f%%", v); }
}
