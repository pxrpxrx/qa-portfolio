package com.tradingtabs.model;

import com.tradingtabs.horizon.HorizonMatrix.*;
import java.time.LocalDate;
import java.util.*;

public class DashboardData {
    public LocalDate date;
    public double btcPrice, fairValue;
    public List<MetricRow> metrics;
    public HorizonView shortTerm, mediumTerm, longTerm;
    public MicroSection micro;
    public List<Scenario> scenarios;
    public List<String> divergences;
    public String macroStatus, btcStatus;
    public List<MetricRow> frameworkRows;
}
