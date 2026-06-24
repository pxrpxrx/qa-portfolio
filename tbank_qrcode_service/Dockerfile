FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/payment-api-3.0.jar app.jar
EXPOSE 8080
ENV TINKOFF_SECRET_KEY=""
ENV TINKOFF_TERMINAL_KEY=""
ENV SPRING_DATASOURCE_PASSWORD=""
ENTRYPOINT ["java", "-jar", "app.jar"]
