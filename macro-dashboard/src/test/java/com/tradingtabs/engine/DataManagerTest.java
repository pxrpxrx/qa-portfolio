package com.tradingtabs.engine;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

@DisplayName("DataManager utility methods")
class DataManagerTest {

    @Nested
    @DisplayName("pctChange()")
    class PctChange {

        @Test
        @DisplayName("returns 0 for null list")
        void nullList() {
            assertThat(DataManager.pctChange(null, 1)).isZero();
        }

        @Test
        @DisplayName("returns 0 for empty list")
        void emptyList() {
            assertThat(DataManager.pctChange(List.of(), 1)).isZero();
        }

        @Test
        @DisplayName("returns 0 when lookback exceeds list size")
        void lookbackTooLarge() {
            assertThat(DataManager.pctChange(List.of(100.0), 5)).isZero();
        }

        @Test
        @DisplayName("calculates positive change correctly")
        void positiveChange() {
            List<Double> values = List.of(100.0, 110.0);
            double result = DataManager.pctChange(values, 1);
            assertThat(result).isCloseTo(0.10, within(0.001));
        }

        @Test
        @DisplayName("calculates negative change correctly")
        void negativeChange() {
            List<Double> values = List.of(100.0, 90.0);
            double result = DataManager.pctChange(values, 1);
            assertThat(result).isCloseTo(-0.10, within(0.001));
        }

        @Test
        @DisplayName("returns 0 when older value is zero")
        void olderValueZero() {
            List<Double> values = List.of(0.0, 100.0);
            assertThat(DataManager.pctChange(values, 1)).isZero();
        }

        @Test
        @DisplayName("handles NaN values gracefully")
        void nanValues() {
            List<Double> values = List.of(Double.NaN, 100.0);
            assertThat(DataManager.pctChange(values, 1)).isZero();
        }

        @Test
        @DisplayName("works with larger lookback")
        void largerLookback() {
            List<Double> values = List.of(100.0, 102.0, 104.0, 106.0, 110.0);
            double result = DataManager.pctChange(values, 4);
            assertThat(result).isCloseTo(0.10, within(0.001));
        }
    }

    @Nested
    @DisplayName("mean()")
    class Mean {

        @Test
        @DisplayName("calculates simple average")
        void simpleAverage() {
            assertThat(DataManager.mean(List.of(1.0, 2.0, 3.0, 4.0, 5.0)))
                .isCloseTo(3.0, within(0.001));
        }

        @Test
        @DisplayName("ignores NaN values")
        void ignoresNan() {
            assertThat(DataManager.mean(List.of(1.0, Double.NaN, 3.0)))
                .isCloseTo(2.0, within(0.001));
        }

        @Test
        @DisplayName("returns 0 for all-NaN list")
        void allNan() {
            assertThat(DataManager.mean(List.of(Double.NaN, Double.NaN))).isZero();
        }

        @Test
        @DisplayName("returns 0 for empty list")
        void emptyList() {
            assertThat(DataManager.mean(List.of())).isZero();
        }
    }

    @Nested
    @DisplayName("std()")
    class Std {

        @Test
        @DisplayName("calculates standard deviation")
        void basicStd() {
            List<Double> values = List.of(2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0);
            double result = DataManager.std(values);
            assertThat(result).isCloseTo(2.138, within(0.01));
        }

        @Test
        @DisplayName("returns 0 for single value")
        void singleValue() {
            assertThat(DataManager.std(List.of(5.0))).isZero();
        }

        @Test
        @DisplayName("returns 0 for identical values")
        void identicalValues() {
            assertThat(DataManager.std(List.of(3.0, 3.0, 3.0))).isZero();
        }
    }

    @Nested
    @DisplayName("zScore()")
    class ZScore {

        @Test
        @DisplayName("returns 0 for value equal to mean")
        void atMean() {
            List<Double> pop = List.of(1.0, 2.0, 3.0, 4.0, 5.0);
            assertThat(DataManager.zScore(3.0, pop)).isCloseTo(0.0, within(0.001));
        }

        @Test
        @DisplayName("returns positive for value above mean")
        void aboveMean() {
            List<Double> pop = List.of(1.0, 2.0, 3.0, 4.0, 5.0);
            assertThat(DataManager.zScore(5.0, pop)).isPositive();
        }

        @Test
        @DisplayName("returns negative for value below mean")
        void belowMean() {
            List<Double> pop = List.of(1.0, 2.0, 3.0, 4.0, 5.0);
            assertThat(DataManager.zScore(1.0, pop)).isNegative();
        }

        @Test
        @DisplayName("returns 0 when std is zero")
        void zeroStd() {
            List<Double> pop = List.of(3.0, 3.0, 3.0);
            assertThat(DataManager.zScore(5.0, pop)).isZero();
        }
    }

    @Nested
    @DisplayName("priorValue()")
    class PriorValue {

        @Test
        @DisplayName("returns correct prior value")
        void correctPrior() {
            List<Double> list = List.of(10.0, 20.0, 30.0, 40.0, 50.0);
            assertThat(DataManager.priorValue(list, 2)).isCloseTo(30.0, within(0.001));
        }

        @Test
        @DisplayName("returns NaN when offset exceeds list size")
        void offsetTooLarge() {
            List<Double> list = List.of(10.0, 20.0);
            assertThat(DataManager.priorValue(list, 5)).isNaN();
        }

        @Test
        @DisplayName("returns NaN for null list")
        void nullList() {
            assertThat(DataManager.priorValue(null, 1)).isNaN();
        }
    }
}
