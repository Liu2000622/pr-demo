FROM eclipse-temurin:17-jdk AS build
WORKDIR /app
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /root/.m2 && echo '<settings><mirrors><mirror><id>aliyun</id><mirrorOf>*</mirrorOf><url>https://maven.aliyun.com/repository/public</url></mirror></mirrors></settings>' > /root/.m2/settings.xml
COPY pom.xml .
COPY scaffold-app/pom.xml scaffold-app/
COPY scaffold-app/src scaffold-app/src
RUN mvn clean package -DskipTests -B

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/scaffold-app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
