package com.tradingtabs.gann;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

@DisplayName("GannSquare9 calculations")
class GannSquare9Test {

    @Nested
    @DisplayName("priceToAngle()")
    class PriceToAngle {

        @Test
        @DisplayName("returns 0 for zero price")
        void zeroPrice() {
            assertThat(GannSquare9.priceToAngle(0)).isZero();
        }

        @Test
        @DisplayName("returns 0 for negative price")
        void negativePrice() {
            assertThat(GannSquare9.priceToAngle(-100)).isZero();
        }

        @Test
        @DisplayName("returns angle in 0-360 range for valid price")
        void validPriceRange() {
            double angle = GannSquare9.priceToAngle(60000);
            assertThat(angle).isBetween(0.0, 360.0);
        }

        @Test
        @DisplayName("different prices produce different angles")
        void differentPricesDifferentAngles() {
            double angle1 = GannSquare9.priceToAngle(50000);
            double angle2 = GannSquare9.priceToAngle(60000);
            assertThat(angle1).isNotEqualTo(angle2);
        }

        @Test
        @DisplayName("BTC price 60000 produces deterministic angle")
        void btcPriceAngle() {
            double angle = GannSquare9.priceToAngle(60000);
            // Verify the angle is deterministic and in valid range
            assertThat(angle).isBetween(0.0, 360.0);
            // Verify same input produces same output
            assertThat(GannSquare9.priceToAngle(60000)).isEqualTo(angle);
        }
    }

    @Nested
    @DisplayName("angleToPrice()")
    class AngleToPrice {

        @Test
        @DisplayName("returns positive price for valid angle and ring")
        void validAngleAndRing() {
            double price = GannSquare9.angleToPrice(90, 100);
            assertThat(price).isPositive();
        }

        @Test
        @DisplayName("higher ring produces higher price at same angle")
        void higherRingHigherPrice() {
            double price1 = GannSquare9.angleToPrice(90, 100);
            double price2 = GannSquare9.angleToPrice(90, 110);
            assertThat(price2).isGreaterThan(price1);
        }

        @Test
        @DisplayName("different angles at same ring produce different prices")
        void differentAnglesDifferentPrices() {
            double price1 = GannSquare9.angleToPrice(0, 100);
            double price2 = GannSquare9.angleToPrice(90, 100);
            assertThat(price1).isNotEqualTo(price2);
        }
    }

    @Nested
    @DisplayName("getSupportResistance()")
    class SupportResistance {

        @Test
        @DisplayName("returns non-empty list for valid price")
        void nonEmptyList() {
            List<GannSquare9.Level> levels = GannSquare9.getSupportResistance(60000, 3, 3);
            assertThat(levels).isNotEmpty();
        }

        @Test
        @DisplayName("levels are sorted by price ascending")
        void sortedByPrice() {
            List<GannSquare9.Level> levels = GannSquare9.getSupportResistance(60000, 3, 3);
            for (int i = 1; i < levels.size(); i++) {
                assertThat(levels.get(i).price()).isGreaterThan(levels.get(i - 1).price());
            }
        }

        @Test
        @DisplayName("contains both support and resistance levels")
        void containsSupportAndResistance() {
            double price = 60000;
            List<GannSquare9.Level> levels = GannSquare9.getSupportResistance(price, 3, 3);

            boolean hasSupport = levels.stream().anyMatch(l -> l.price() < price);
            boolean hasResistance = levels.stream().anyMatch(l -> l.price() > price);

            assertThat(hasSupport).isTrue();
            assertThat(hasResistance).isTrue();
        }

        @Test
        @DisplayName("all levels have valid cross type")
        void validCrossType() {
            List<GannSquare9.Level> levels = GannSquare9.getSupportResistance(60000, 3, 3);
            for (GannSquare9.Level level : levels) {
                assertThat(level.cross()).isIn("CARDINAL", "FIXED");
            }
        }
    }

    @Nested
    @DisplayName("formatBlock()")
    class FormatBlock {

        @Test
        @DisplayName("returns non-empty formatted output")
        void nonEmptyOutput() {
            List<String> lines = GannSquare9.formatBlock(60000);
            assertThat(lines).isNotEmpty();
        }

        @Test
        @DisplayName("contains price information")
        void containsPriceInfo() {
            List<String> lines = GannSquare9.formatBlock(60000);
            String output = String.join("\n", lines);
            assertThat(output).contains("Price:");
            assertThat(output).contains("Ring:");
            assertThat(output).contains("Angle:");
        }

        @Test
        @DisplayName("contains key levels section")
        void containsKeyLevels() {
            List<String> lines = GannSquare9.formatBlock(60000);
            String output = String.join("\n", lines);
            assertThat(output).contains("Key levels:");
        }

        @Test
        @DisplayName("contains squared prices section")
        void containsSquaredPrices() {
            List<String> lines = GannSquare9.formatBlock(60000);
            String output = String.join("\n", lines);
            assertThat(output).contains("Squared prices:");
        }
    }

    @Nested
    @DisplayName("shortSummary()")
    class ShortSummary {

        @Test
        @DisplayName("returns formatted summary string")
        void formattedSummary() {
            String summary = GannSquare9.shortSummary(60000);
            // Locale-independent: just check structure
            assertThat(summary).contains("Ring");
            assertThat(summary).containsAnyOf("CARDINAL", "FIXED");
        }

        @Test
        @DisplayName("contains cross type")
        void containsCrossType() {
            String summary = GannSquare9.shortSummary(60000);
            assertThat(summary).containsAnyOf("CARDINAL", "FIXED");
        }
    }

    @Nested
    @DisplayName("Level record")
    class LevelRecord {

        @Test
        @DisplayName("label() formats correctly")
        void labelFormats() {
            GannSquare9.Level level = new GannSquare9.Level(60000, 90, "CARDINAL");
            String label = level.label();
            // Locale-independent: check structural elements
            assertThat(label).contains("90");
            assertThat(label).contains("CARDINAL");
        }
    }
}
