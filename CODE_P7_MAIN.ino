/*
 * ARDUINO MEGA 2560 - PHÂN LOẠI & LƯU KHO ĐAI ỐC AUTOMATION
 */

// ==========================================
// ĐỊNH NGHĨA CHÂN ĐIỀU KHIỂN (PINS)
// ==========================================
#define CYLINDER_M8_PIN   24
#define CYLINDER_M12_PIN  22

#define X_LIMIT_PIN       26
#define Z_LIMIT_PIN       28

#define X_STEP_PIN        2
#define X_DIR_PIN         3

#define Y_STEP_PIN        30
#define Y_DIR_PIN         32

#define Z_STEP_PIN        4
#define Z_DIR_PIN         5

// ==========================================
// THÔNG SỐ TỐC ĐỘ & GIA TỐC AUTO
// ==========================================
const int MAX_DELAY_US = 500;  // Delay khởi đầu / kết thúc (chậm)
const int MIN_DELAY_US = 100;  // Delay tốc độ tối đa (nhanh)
const int ACCEL_STEPS  = 300;  

// ==========================================
// THÔNG SỐ JOG BẰNG TAY (MANUAL)
// ==========================================
const int JOG_START_DELAY = 600; 
const int JOG_MAX_DELAY   = 150; 
const int JOG_ACCEL_STEP  = 2;   
int currentJogDelay       = JOG_START_DELAY;

// ==========================================
// BIẾN TRẠNG THÁI HỆ THỐNG
// ==========================================
long current_X = 0;
long current_Y = 0;
long current_Z = 0;

bool isJogging = false;
char jogAxis = ' ';
char jogDir = ' ';

bool isStopped = false; // Cờ dừng hệ thống khẩn cấp

// TỌA ĐỘ XUNG CỐ ĐỊNH
const long Y_SAFE        = 0;
const long Y_PICKUP      = 5750;  
const long Y_STORE       = -4980; 
const long Y_EXPORT_OUT  = -6330; 

const long Z_PICKUP_LOW  = 0;
const long Z_PICKUP_HIGH = 1934;

const long Z_TANG1_LOW   = 0;
const long Z_TANG1_HIGH  = 7660;

const long Z_TANG2_LOW   = 7660;
const long Z_TANG2_HIGH  = 14606;

const long Z_EXPORT_LOW  = 0;
const long Z_EXPORT_HIGH = 5550;

const long X_PICKUP_M8   = 15365;
const long X_PICKUP_M12  = 7428;

const long X_COL[4]      = {6120, 10235, 14417, 18488}; 
const long X_EXPORT      = 195; 

// Trạng thái lưu trữ 8 ô kho (Mặc định khi bật nguồn là trống hết)
bool warehouseOccupied[8] = {false};

// Buffer nhận dữ liệu Serial
char serialBuffer[64];
int bufferIdx = 0;

// Biến điều khiển xilanh Non-blocking
unsigned long cylM8Timer = 0;
unsigned long cylM12Timer = 0;
bool cylM8Active = false;
bool cylM12Active = false;

// ==========================================
// PROTOTYPES
// ==========================================
void sendStep(int stepPin, int delayUs);
void reportPulse();
void triggerCylinder(int pin);
void updateCylinders();
void homeZ();
void homeX();
void homeY();
bool moveXTo(long targetX);
bool moveYTo(long targetY);
bool moveZTo(long targetZ);
void doContinuousJog();
void stopJogSmoothly();
void executeStoreProcess(int type);
void executeExportProcess(int slotIdx);
void processCommand(char* cmd);

// ==========================================
// SETUP & LOOP MAIN
// ==========================================
void setup() {
  Serial.begin(115200);

  pinMode(CYLINDER_M8_PIN, OUTPUT);
  pinMode(CYLINDER_M12_PIN, OUTPUT);
  digitalWrite(CYLINDER_M8_PIN, LOW);
  digitalWrite(CYLINDER_M12_PIN, LOW);

  pinMode(X_LIMIT_PIN, INPUT_PULLUP);
  pinMode(Z_LIMIT_PIN, INPUT_PULLUP);

  pinMode(X_STEP_PIN, OUTPUT); pinMode(X_DIR_PIN, OUTPUT);
  pinMode(Y_STEP_PIN, OUTPUT); pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Z_STEP_PIN, OUTPUT); pinMode(Z_DIR_PIN, OUTPUT);

  // Khởi tạo trạng thái kho trống ban đầu
  for (int i = 0; i < 8; i++) {
    warehouseOccupied[i] = false;
  }

  Serial.println("SYSTEM_READY");
}

void loop() {
  // Cập nhật trạng thái xilanh (Non-blocking)
  updateCylinders();

  // Đọc dữ liệu từ Serial (Non-blocking)
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (bufferIdx > 0) {
        serialBuffer[bufferIdx] = '\0';
        processCommand(serialBuffer);
        bufferIdx = 0;
      }
    } else if (bufferIdx < 63) {
      serialBuffer[bufferIdx++] = c;
    }
  }

  // Thực thi Jog liên tục
  if (isJogging && !isStopped) {
    doContinuousJog();
  }

  // Báo cáo tọa độ định kỳ
  static unsigned long lastReport = 0;
  if (!isJogging && (millis() - lastReport > 200)) {
    lastReport = millis();
    reportPulse();
  }
}

// ==========================================
// XỬ LÝ LỆNH TỪ PYTHON
// ==========================================
void processCommand(char* cmd) {
  String cmdStr = String(cmd);
  cmdStr.trim();

  if (cmdStr == "STOP" || cmdStr == "EMERGENCY_STOP") {
    isStopped = true;
    isJogging = false;
    Serial.println("SYSTEM_STOPPED");
    return;
  }

  if (cmdStr == "RESUME" || cmdStr == "RESET_STOP") {
    isStopped = false;
    Serial.println("SYSTEM_RESUMED");
    return;
  }

  if (isStopped) {
    Serial.println("ERROR: SYSTEM_IS_STOPPED");
    return;
  }

  if (cmdStr == "HOME_Z") { isJogging = false; homeZ(); }
  else if (cmdStr == "HOME_X") { isJogging = false; homeX(); }
  else if (cmdStr == "HOME_Y") { isJogging = false; homeY(); }
  else if (cmdStr == "HOME_ALL") { isJogging = false; homeZ(); homeX(); homeY(); }
  else if (cmdStr == "CYL_M8") { triggerCylinder(CYLINDER_M8_PIN); }
  else if (cmdStr == "CYL_M12") { triggerCylinder(CYLINDER_M12_PIN); }
  
  else if (cmdStr.startsWith("START_JOG_")) {
    jogAxis = cmdStr.charAt(10);
    jogDir = cmdStr.charAt(12);
    currentJogDelay = JOG_START_DELAY;
    isJogging = true;
  }
  else if (cmdStr == "STOP_JOG") {
    if (isJogging) {
      stopJogSmoothly();
      isJogging = false;
      reportPulse();
    }
  }
  
  else if (cmdStr == "STORE_M8") { executeStoreProcess(8); }
  else if (cmdStr == "STORE_M12") { executeStoreProcess(12); }
  
  else if (cmdStr.startsWith("EXPORT_")) {
    int slot = cmdStr.substring(7).toInt();
    executeExportProcess(slot);
  }
  else if (cmdStr == "RESET_WAREHOUSE") {
    for (int i = 0; i < 8; i++) warehouseOccupied[i] = false;
    Serial.println("WAREHOUSE_RESET_OK");
  }
}

// ==========================================
// HÀM ĐIỀU KHIỂN ĐỘNG CƠ CƠ BẢN & XILANH
// ==========================================
void sendStep(int stepPin, int delayUs) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(delayUs);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(delayUs);
}

void reportPulse() {
  Serial.print("P:");
  Serial.print(current_X); Serial.print(",");
  Serial.print(current_Y); Serial.print(",");
  Serial.println(current_Z);
}

void triggerCylinder(int pin) {
  digitalWrite(pin, HIGH);
  if (pin == CYLINDER_M8_PIN) {
    cylM8Active = true;
    cylM8Timer = millis();
  } else if (pin == CYLINDER_M12_PIN) {
    cylM12Active = true;
    cylM12Timer = millis();
  }
}

void updateCylinders() {
  if (cylM8Active && (millis() - cylM8Timer >= 500)) {
    digitalWrite(CYLINDER_M8_PIN, LOW);
    cylM8Active = false;
  }
  if (cylM12Active && (millis() - cylM12Timer >= 500)) {
    digitalWrite(CYLINDER_M12_PIN, LOW);
    cylM12Active = false;
  }
}

// ==========================================
// CHUẨN HÓA HOME VỀ GỐC
// ==========================================
void homeZ() {
  digitalWrite(Z_DIR_PIN, HIGH);
  long timeoutSteps = 100000;
  while (digitalRead(Z_LIMIT_PIN) == HIGH && timeoutSteps > 0 && !isStopped) {
    sendStep(Z_STEP_PIN, 300);
    timeoutSteps--;
  }
  current_Z = 0;
  reportPulse();
}

void homeX() {
  digitalWrite(X_DIR_PIN, HIGH);
  long timeoutSteps = 100000;
  while (digitalRead(X_LIMIT_PIN) == HIGH && timeoutSteps > 0 && !isStopped) {
    sendStep(X_STEP_PIN, 300);
    timeoutSteps--;
  }
  current_X = 0;
  reportPulse();
}

void homeY() {
  current_Y = 0;
  reportPulse();
}

// ==========================================
// HÀM DI CHUYỂN AUTO VỚI GIA TỐC
// ==========================================
bool moveXTo(long targetX) {
  long delta = targetX - current_X;
  if (delta == 0) return true;

  digitalWrite(X_DIR_PIN, (delta > 0) ? LOW : HIGH);
  long totalSteps = abs(delta);
  long rampSteps = min((long)ACCEL_STEPS, totalSteps / 2);

  for (long i = 0; i < totalSteps; i++) {
    if (isStopped) return false;
    if (digitalRead(X_LIMIT_PIN) == LOW && (delta < 0)) break;

    int currentDelay = MIN_DELAY_US;
    if (i < rampSteps) {
      currentDelay = map(i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    } else if (i >= totalSteps - rampSteps) {
      currentDelay = map(totalSteps - i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    }

    sendStep(X_STEP_PIN, currentDelay);
    current_X += (delta > 0) ? 1 : -1;
  }
  return true;
}

bool moveYTo(long targetY) {
  long delta = targetY - current_Y;
  if (delta == 0) return true;

  digitalWrite(Y_DIR_PIN, (delta > 0) ? HIGH : LOW);
  long totalSteps = abs(delta);
  long rampSteps = min((long)ACCEL_STEPS, totalSteps / 2);

  for (long i = 0; i < totalSteps; i++) {
    if (isStopped) return false;

    int currentDelay = MIN_DELAY_US;
    if (i < rampSteps) {
      currentDelay = map(i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    } else if (i >= totalSteps - rampSteps) {
      currentDelay = map(totalSteps - i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    }

    sendStep(Y_STEP_PIN, currentDelay);
    current_Y += (delta > 0) ? 1 : -1;
  }
  return true;
}

bool moveZTo(long targetZ) {
  long delta = targetZ - current_Z;
  if (delta == 0) return true;

  digitalWrite(Z_DIR_PIN, (delta > 0) ? LOW : HIGH);
  long totalSteps = abs(delta);
  long rampSteps = min((long)ACCEL_STEPS, totalSteps / 2);

  for (long i = 0; i < totalSteps; i++) {
    if (isStopped) return false;
    if (digitalRead(Z_LIMIT_PIN) == LOW && (delta < 0)) break;

    int currentDelay = MIN_DELAY_US;
    if (i < rampSteps) {
      currentDelay = map(i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    } else if (i >= totalSteps - rampSteps) {
      currentDelay = map(totalSteps - i, 0, rampSteps, MAX_DELAY_US, MIN_DELAY_US);
    }

    sendStep(Z_STEP_PIN, currentDelay);
    current_Z += (delta > 0) ? 1 : -1;
  }
  return true;
}

// ==========================================
// CHẾ ĐỘ JOG BẰNG TAY
// ==========================================
void doContinuousJog() {
  int stepPin = -1;
  
  if (jogAxis == 'X') {
    if (jogDir == '-' && digitalRead(X_LIMIT_PIN) == LOW) { isJogging = false; return; }
    digitalWrite(X_DIR_PIN, (jogDir == '+') ? LOW : HIGH);
    stepPin = X_STEP_PIN;
  } 
  else if (jogAxis == 'Y') {
    digitalWrite(Y_DIR_PIN, (jogDir == '+') ? HIGH : LOW);
    stepPin = Y_STEP_PIN;
  } 
  else if (jogAxis == 'Z') {
    if (jogDir == '-' && digitalRead(Z_LIMIT_PIN) == LOW) { isJogging = false; return; }
    digitalWrite(Z_DIR_PIN, (jogDir == '+') ? LOW : HIGH);
    stepPin = Z_STEP_PIN;
  }

  if (stepPin != -1) {
    sendStep(stepPin, currentJogDelay);

    if (jogAxis == 'X') current_X += (jogDir == '+') ? 1 : -1;
    else if (jogAxis == 'Y') current_Y += (jogDir == '+') ? 1 : -1;
    else if (jogAxis == 'Z') current_Z += (jogDir == '+') ? 1 : -1;

    if (currentJogDelay > JOG_MAX_DELAY) {
      currentJogDelay -= JOG_ACCEL_STEP;
      if (currentJogDelay < JOG_MAX_DELAY) currentJogDelay = JOG_MAX_DELAY;
    }
  }
}

void stopJogSmoothly() {
  int stepPin = -1;
  if (jogAxis == 'X') stepPin = X_STEP_PIN;
  else if (jogAxis == 'Y') stepPin = Y_STEP_PIN;
  else if (jogAxis == 'Z') stepPin = Z_STEP_PIN;

  if (stepPin == -1) return;

  while (currentJogDelay < JOG_START_DELAY && !isStopped) {
    sendStep(stepPin, currentJogDelay);
    if (jogAxis == 'X') current_X += (jogDir == '+') ? 1 : -1;
    else if (jogAxis == 'Y') current_Y += (jogDir == '+') ? 1 : -1;
    else if (jogAxis == 'Z') current_Z += (jogDir == '+') ? 1 : -1;

    currentJogDelay += (JOG_ACCEL_STEP * 3);
  }
}

// ==========================================
// CHUỖI TỰ ĐỘNG CẤT HÀNG (STORE PROCESS)
// ==========================================
void executeStoreProcess(int type) {
  int targetSlot = -1;

  if (type == 8) {
    for (int i = 0; i < 4; i++) {
      if (!warehouseOccupied[i]) { targetSlot = i; break; }
    }
  } else if (type == 12) {
    for (int i = 4; i < 8; i++) {
      if (!warehouseOccupied[i]) { targetSlot = i; break; }
    }
  }

  if (targetSlot == -1) {
    Serial.println("ERROR: WAREHOUSE_SECTION_FULL");
    return;
  }

  long targetX = X_COL[targetSlot % 4];
  long targetZ_Low = (targetSlot < 4) ? Z_TANG1_LOW : Z_TANG2_LOW;
  long targetZ_High = (targetSlot < 4) ? Z_TANG1_HIGH : Z_TANG2_HIGH;
  long pickupX = (type == 8) ? X_PICKUP_M8 : X_PICKUP_M12;

  // 1. LẤY HÀNG TỪ BĂNG TẢI
  if (!moveYTo(Y_SAFE)) return;
  if (!moveZTo(Z_PICKUP_LOW)) return;
  if (!moveXTo(pickupX)) return;
  delay(200);

  if (!moveYTo(Y_PICKUP)) return;
  delay(200);
  if (!moveZTo(Z_PICKUP_HIGH)) return;
  delay(200);
  if (!moveYTo(Y_SAFE)) return;
  delay(200);

  // 2. ĐẶT HÀNG VÀO Ô KHO
  if (!moveZTo(targetZ_High)) return;
  if (!moveXTo(targetX)) return;
  delay(200);

  if (!moveYTo(Y_STORE)) return;
  delay(200);
  if (!moveZTo(targetZ_Low)) return;
  delay(200);
  if (!moveYTo(Y_SAFE)) return;

  homeZ();
  homeX();
  homeY();

  warehouseOccupied[targetSlot] = true;
  reportPulse();

  Serial.print("STORE_DONE:");
  Serial.println(targetSlot);
}

// ==========================================
// CHUỖI TỰ ĐỘNG XUẤT HÀNG (EXPORT PROCESS)
// ==========================================
void executeExportProcess(int slotIdx) {
  if (slotIdx < 0 || slotIdx >= 8 || !warehouseOccupied[slotIdx]) {
    Serial.println("ERROR: INVALID_SLOT_OR_EMPTY");
    return;
  }

  long srcX = X_COL[slotIdx % 4];
  long srcZ_Low = (slotIdx < 4) ? Z_TANG1_LOW : Z_TANG2_LOW;
  long srcZ_High = (slotIdx < 4) ? Z_TANG1_HIGH : Z_TANG2_HIGH;

  // 1. LẤY HÀNG TỪ Ô KHO
  if (!moveYTo(Y_SAFE)) return;
  if (!moveZTo(srcZ_Low)) return;
  if (!moveXTo(srcX)) return;
  delay(200);

  if (!moveYTo(Y_STORE)) return;
  delay(200);
  if (!moveZTo(srcZ_High)) return;
  delay(200);
  if (!moveYTo(Y_SAFE)) return;
  delay(200);

  // 2. ĐƯA RA CỬA XUẤT HÀNG
  if (!moveZTo(Z_EXPORT_HIGH)) return;
  if (!moveXTo(X_EXPORT)) return;
  delay(200);

  if (!moveYTo(Y_EXPORT_OUT)) return;
  delay(200);
  if (!moveZTo(Z_EXPORT_LOW)) return;
  delay(200);
  if (!moveYTo(Y_SAFE)) return;

  homeZ();
  homeX();
  homeY();

  warehouseOccupied[slotIdx] = false;
  reportPulse();

  Serial.print("EXPORT_DONE:");
  Serial.println(slotIdx);
}


