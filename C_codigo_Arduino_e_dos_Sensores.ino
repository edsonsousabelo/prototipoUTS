#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Definições dos Pinos
#define DHTPIN 12
#define DHTTYPE DHT22
#define ONE_WIRE_BUS 3
const int pinoUmiA = A0;
const int pinoUmiB = A1;

// Inicialização dos Sensores
DHT dht(DHTPIN, DHTTYPE);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensorSolo(&oneWire);

void setup() {
  Serial.begin(9600);
  dht.begin();
  sensorSolo.begin();
  Serial.println("--- Sistema Iniciado: Monitoramento em Redundancia ---");
}

void loop() {
  // 1. Leitura da Umidade do Solo (Redundância)
  int leituraA = analogRead(pinoUmiA);
  int leituraB = analogRead(pinoUmiB);
  
  // Converte para porcentagem (considerando 1023 seco e 0 molhado)
  int umiA = map(leituraA, 1023, 0, 0, 100);
  int umiB = map(leituraB, 1023, 0, 0, 100);
  
  // Média para redundância
  int mediaUmidade = ((umiA + umiB) / 2);

  // 2. Leitura da Temperatura do Solo (DS18B20)
  sensorSolo.requestTemperatures(); 
  float tempSoloC = sensorSolo.getTempCByIndex(0);

  // 3. Leitura da Temperatura Externa (DHT22)
  float tempArC = dht.readTemperature();
  float humiAr = dht.readHumidity();

  // --- EXIBIÇÃO DOS DADOS ---
  Serial.println("====================================");
  Serial.print("Solo - Umidade Media: "); Serial.print(mediaUmidade); Serial.println("%");
  Serial.print("Solo - Temp. (DS18B20-interno): "); Serial.print(tempSoloC); Serial.println(" C");
  Serial.print("Ar   - Temp. (DHT22-externo): "); Serial.print(tempArC); Serial.println(" C");
  Serial.print("Ar   - Umid. Relativa: "); Serial.print(humiAr); Serial.println("%");
  
  // Verificação de Redundância (Alerta se os sensores divergirem muito)
  if (abs(umiA - umiB) > 20) {
    Serial.println("AVISO: Alta divergencia entre sensores de solo!");
  }
  
  delay(3000); // Aguarda 3 segundos para a próxima leitura
}