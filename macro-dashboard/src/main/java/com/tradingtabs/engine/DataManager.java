package com.tradingtabs.engine;

import com.tradingtabs.data.*;
import com.tradingtabs.macro.MacroDataClient;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;


public class DataManager {
    private final FredClient fred;
    private final CryptoClient crypto;
    private final MacroDataClient macro;

    public DataManager() {
        this.fred = new FredClient();
        this.crypto = new CryptoClient();
        this.macro = new MacroDataClient();
    }

    public record Snapshot(
        LocalDate date,
        double iorb, double m2, double tga, double onrrp, double gdp,
        double baa10y, double dgs10, double dgs3mo, double dgs2,
        double deficit, double unrate, double dxy,
        double spx, double ndx, double gld, double tlt, double hyg, double nvda,
        double xlk, double xlu, double xly, double xlp, double xlf, double vix,
        double sofr, double mortgage30, double pce, double t5yie, double fedBalance,
        double shy, double icln, double lac, double ita, double arkx,
        double bx, double blk, double ng, double srln,
        double copper, double oil, double silver, double totalDebt,
        double iwm,
        double dji, double cat, double xli,
        double btcPrice, double btcFunding, double btcVolume, double btcOi,
        Map<String,Double> priors,
        List<Double> m2History, List<Double> dxyHistory, List<Double> btcHistory,
        List<Double> spxHistory, List<Double> gldHistory, List<Double> tltHistory,
        List<Double> vixHistory, List<Double> hygHistory, List<Double> nvdaHistory,
        List<Double> xlkHistory, List<Double> xluHistory, List<Double> xlyHistory,
        List<Double> xlpHistory, List<Double> xlfHistory,
        List<Double> sofrHistory, List<Double> mortgage30History,
        List<Double> fedBalanceHistory, List<Double> shyHistory, List<Double> ngHistory,
        List<Double> totalDebtHistory,
        List<Double> dgs2History, List<Double> t5yieHistory, List<Double> iwmHistory,
        List<Double> ndxHistory, List<Double> copperHistory,
        List<Double> djiHistory, List<Double> catHistory, List<Double> xliHistory,
        List<Double> srlnHistory
    ) {}

    public Snapshot fetchAll() {
        LocalDate now = LocalDate.now();
        CryptoClient.Ticker ticker = crypto.fetchBtcTicker();
        MacroDataClient.PriceSnapshot prices = macro.fetchAll();

        LocalDate mo = now.minusMonths(3);
        List<Double> m2Hist = fred.fetchSeries("M2SL", mo, now)
            .stream().map(o -> scale(o.value(), 1000)).toList();
        List<Double> dxyHist = fred.fetchSeries("DTWEXBGS", now.minusDays(30), now)
            .stream().map(o -> o.value()).toList();

        List<Double> btcHist = fetchBtcHistory(30);

        // Fetch Yahoo histories
        List<Double> spxHist = fetchYahooHist("SPY", 30);
        List<Double> gldHist = fetchYahooHist("GLD", 30);
        List<Double> tltHist = fetchYahooHist("TLT", 30);
        List<Double> vixHist = fetchYahooHist("^VIX", 30);
        List<Double> hygHist = fetchYahooHist("HYG", 30);
        List<Double> nvdaHist = fetchYahooHist("NVDA", 30);
        List<Double> xlkHist = fetchYahooHist("XLK", 30);
        List<Double> xluHist = fetchYahooHist("XLU", 30);
        List<Double> xlyHist = fetchYahooHist("XLY", 30);
        List<Double> xlpHist = fetchYahooHist("XLP", 30);
        List<Double> xlfHist = fetchYahooHist("XLF", 30);

        double rawM2 = fred.fetchLatestValue("M2SL");
        double rawTga = fred.fetchLatestValue("WTREGEN");
        double rawRrp = fred.fetchLatestValue("RRPONTSYD");

        // FRED series
        LocalDate mo90 = now.minusMonths(3);
        double rawSofr = fred.fetchLatestValue("SOFR");
        double rawMortgage30 = fred.fetchLatestValue("MORTGAGE30US");
        double rawPce = fred.fetchLatestValue("PCEPILFE");
        double rawFedBal = fred.fetchLatestValue("WALCL");
        List<Double> sofrHist = fred.fetchSeries("SOFR", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> mortgage30Hist = fred.fetchSeries("MORTGAGE30US", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> fedBalanceHist = fred.fetchSeries("WALCL", mo90, now)
            .stream().map(o -> o.value()).toList();

        // New FRED histories for priors
        List<Double> iorbHist = fred.fetchSeries("IORB", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> tgaHist = fred.fetchSeries("WTREGEN", mo90, now)
            .stream().map(o -> scale(o.value(), 1_000_000)).toList();
        List<Double> onrrpHist = fred.fetchSeries("RRPONTSYD", mo90, now)
            .stream().map(o -> scale(o.value(), 1000)).toList();
        List<Double> dgs10Hist = fred.fetchSeries("DGS10", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> dgs3moHist = fred.fetchSeries("DGS3MO", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> baa10yHist = fred.fetchSeries("BAA10Y", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> pceHist = fred.fetchSeries("PCEPILFE", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> deficitHist = fred.fetchSeries("FYFSD", mo90, now)
            .stream().map(o -> scale(o.value(), 1_000_000)).toList();
        List<Double> dgs2Hist = fred.fetchSeries("DGS2", mo90, now)
            .stream().map(o -> o.value()).toList();
        List<Double> t5yieHist = fred.fetchSeries("T5YIE", mo90, now)
            .stream().map(o -> o.value()).toList();

        // Yahoo histories
        List<Double> shyHist = fetchYahooHist("SHY", 30);
        List<Double> ngHist = fetchYahooHist("NG=F", 30);
        List<Double> copperHist = fetchYahooHist("CPER", 30);
        List<Double> oilHist = fetchYahooHist("USO", 30);
        List<Double> silverHist = fetchYahooHist("SLV", 30);
        List<Double> iwmHist = fetchYahooHist("IWM", 30);
        List<Double> ndxHist = fetchYahooHist("QQQ", 30);
        List<Double> djiHist = fetchYahooHist("^DJI", 30);
        List<Double> catHist = fetchYahooHist("CAT", 30);
        List<Double> xliHist = fetchYahooHist("XLI", 30);
        List<Double> srlnHist = fetchYahooHist("SRLN", 30);

        // Fiscal data
        double rawTotalDebt = fred.fetchLatestValue("GFDEBTN");
        List<Double> totalDebtHist = fred.fetchSeries("GFDEBTN", mo90, now)
            .stream().map(o -> scale(o.value(), 1_000_000)).toList();

        // Build priors map (level offset for trend detection: 5d for daily, 1 for monthly)
        Map<String,Double> priors = new HashMap<>();
        priors.put("iorb", priorValue(iorbHist, 5));
        priors.put("tga", priorValue(tgaHist, 5));
        priors.put("onrrp", priorValue(onrrpHist, 5));
        priors.put("dgs10", priorValue(dgs10Hist, 5));
        priors.put("dgs3mo", priorValue(dgs3moHist, 5));
        priors.put("baa10y", priorValue(baa10yHist, 5));
        priors.put("dgs2", priorValue(dgs2Hist, 5));
        priors.put("t5yie", priorValue(t5yieHist, 5));
        priors.put("copper", priorValue(copperHist, 5));
        priors.put("oil", priorValue(oilHist, 5));
        priors.put("silver", priorValue(silverHist, 5));
        priors.put("iwm", priorValue(iwmHist, 5));
        // Monthly series: use offset 1 (1 observation back)
        priors.put("pce", priorValue(pceHist, 1));
        priors.put("deficit", priorValue(deficitHist, 1));
        priors.put("mortgage30", priorValue(mortgage30Hist, 5));
        priors.put("srln", priorValue(srlnHist, 5));

        return new Snapshot(
            now,
            fred.fetchLatestValue("IORB"),
            scale(rawM2, 1000),
            scale(rawTga, 1_000_000),
            scale(rawRrp, 1000),
            scale(fred.fetchLatestValue("GDP"), 1000),
            fred.fetchLatestValue("BAA10Y"),
            fred.fetchLatestValue("DGS10"),
            fred.fetchLatestValue("DGS3MO"),
            fred.fetchLatestValue("DGS2"),
            scale(fred.fetchLatestValue("FYFSD"), 1_000_000),
            fred.fetchLatestValue("UNRATE"),
            fred.fetchLatestValue("DTWEXBGS"),
            prices.spx(), prices.ndx(), prices.gld(),
            prices.tlt(), prices.hyg(), prices.nvda(),
            prices.xlk(), prices.xlu(), prices.xly(), prices.xlp(), prices.xlf(), prices.vix(),
            rawSofr, rawMortgage30, rawPce,
            fred.fetchLatestValue("T5YIE"), rawFedBal,
            prices.shy(), prices.icln(), prices.lac(),
            prices.ita(), prices.arkx(), prices.bx(), prices.blk(), prices.ng(), prices.srln(),
            prices.copper(), prices.uso(), prices.slv(), scale(rawTotalDebt, 1_000_000),
            prices.iwm(),
            prices.dji(), prices.cat(), prices.xli(),
            ticker.price(), ticker.fundingRate(), ticker.volume24h(), ticker.oi(),
            Collections.unmodifiableMap(priors),
            m2Hist, dxyHist, btcHist,
            spxHist, gldHist, tltHist, vixHist, hygHist, nvdaHist,
            xlkHist, xluHist, xlyHist, xlpHist, xlfHist,
            sofrHist, mortgage30Hist, fedBalanceHist, shyHist, ngHist,
            totalDebtHist,
            dgs2Hist, t5yieHist, iwmHist,
            ndxHist, copperHist,
            djiHist, catHist, xliHist,
            srlnHist
        );
    }

    public static double priorValue(List<Double> list, int offsetFromEnd) {
        if (list == null || list.size() < offsetFromEnd + 1) return Double.NaN;
        double v = list.get(list.size() - 1 - offsetFromEnd);
        return Double.isNaN(v) ? Double.NaN : v;
    }

    private List<Double> fetchYahooHist(String symbol, int days) {
        try {
            Map<LocalDate, Double> hist = macro.fetchHistory(symbol, days);
            if (hist == null || hist.isEmpty()) return List.of();
            List<Map.Entry<LocalDate, Double>> sorted = new ArrayList<>(hist.entrySet());
            sorted.sort(Map.Entry.comparingByKey());
            return sorted.stream().map(e -> e.getValue()).filter(v -> !Double.isNaN(v)).toList();
        } catch (Exception e) { return List.of(); }
    }

    private List<Double> fetchBtcHistory(int days) {
        List<Double> prices = new ArrayList<>();
        try {
            MacroDataClient.PriceSnapshot s = macro.fetchAll();
            prices.add(s.spx() > 0 ? Double.NaN : s.spx());
        } catch (Exception ignored) {}
        try {
            Map<LocalDate, Double> hist = macro.fetchHistory("BTC-USD", days);
            if (hist != null && !hist.isEmpty()) {
                List<Map.Entry<LocalDate, Double>> sorted = new ArrayList<>(hist.entrySet());
                sorted.sort(Map.Entry.comparingByKey());
                for (Map.Entry<LocalDate, Double> e : sorted) {
                    if (!Double.isNaN(e.getValue())) prices.add(e.getValue());
                }
            }
        } catch (Exception ignored) {}
        if (prices.isEmpty()) prices.add(crypto.fetchBtcPrice());
        return prices;
    }

    public static double pctChange(List<Double> values, int lookback) {
        if (values == null || values.size() < lookback + 1) return 0;
        double latest = values.get(values.size() - 1);
        double older = values.get(values.size() - 1 - lookback);
        if (Double.isNaN(latest) || Double.isNaN(older) || older == 0) return 0;
        return (latest - older) / older;
    }

    public static double mean(List<Double> values) {
        return values.stream().filter(v -> !Double.isNaN(v))
            .mapToDouble(v -> v).average().orElse(0);
    }

    public static double std(List<Double> values) {
        double m = mean(values);
        double sum = values.stream().filter(v -> !Double.isNaN(v))
            .mapToDouble(v -> Math.pow(v - m, 2)).sum();
        long count = values.stream().filter(v -> !Double.isNaN(v)).count();
        return count < 2 ? 0 : Math.sqrt(sum / (count - 1));
    }

    public static double zScore(double value, List<Double> population) {
        double m = mean(population);
        double s = std(population);
        return s == 0 ? 0 : (value - m) / s;
    }

    private static double scale(double v, double factor) {
        return Double.isNaN(v) ? Double.NaN : v / factor;
    }
}
