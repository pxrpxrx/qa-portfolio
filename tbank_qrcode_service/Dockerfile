FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY src/payment-api-3.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
