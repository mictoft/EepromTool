/*
 * eepromMemLayout.h
 *
 *  Created on: Jun 9, 2021
 *      Author: michael
 */

#ifndef EEPROMMEMLAYOUT_H_
#define EEPROMMEMLAYOUT_H_


////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// EEPROM MEMORY LAYOUT ///////////////////////////////////

#define MAX_IP_ADDRESS_LEN					16	//15 bytes + 1 x "\0"
#define MAX_SUBNET_ADDRESS_LEN				16	//15 bytes + 1 x "\0"
#define MAX_GATEWAY_ADDRESS_LEN				16	//15 bytes + 1 x "\0"
#define MAX_SNTP_SERVER_ADDRESS_LEN			47

#define MAX_SERIAL_NO_LEN					12	//11 bytes + 1 x "\0"
#define MAX_PCB_SERIAL_NO_LEN				10  //9  bytes + "\0"

#define MAX_AZURE_HOSTNAME					50
#define MAX_AZURE_CON_ID					128
#define MAX_AZURE_CON_KEY					64
#define MAX_AZURE_EKSTRA					57
#define MAX_AZURE_CONNECTION_STRING	    	MAX_AZURE_HOSTNAME + MAX_AZURE_CON_ID + MAX_AZURE_CON_KEY + MAX_AZURE_EKSTRA + 1 //The 1 for '\0' which gives a total of 300 bytes


//HostName=NF-IoT-HUB2.azure-devices.net;DeviceId=14701000002;SharedAccessKey=bVyUdLr4iZGPUeYP0ubSwQ24eU5cEecOzGw+F1ZQ0cU=
//NF-IoT-HUB2.azure-devices.net;14701000002;bVyUdLr4iZGPUeYP0ubSwQ24eU5cEecOzGw+F1ZQ0cU=

#define AZURE_HOSTNAME_STR					"HostName="
#define AZURE_DEVICEID_STR					"DeviceId="
#define AZURE_SHAREDACCESSKEY_STR			"SharedAccessKey="
#define AZURE_SEPERATOR_STR					';'
#define MAX_AZURE_HOSTNAME_USED				50	//Current used HostName = NF-IoT-HUB2.azure-devices.net, this must not exceed 50 bytes + 1 byte for AZURE_SEPERATOR_STR
#define MAX_AZURE_CON_ID_USED				12	//Current DeviceId = "Machine Serial Number", this must not exceed 11 bytes + 1 byte for AZURE_SEPERATOR_STR
#define MAX_AZURE_CON_KEY_USED				76 //The 64 is the max size of the SharedAccessKey at the moment but there is room for 13 bytes more. All unused bytes must be set to \0
#define MAX_CLOUD_CONNECT_PIN_LEN 			4

#define MAX_MAC_ADR_LEN						18

#define MAX_SHA256_SIZE_USED			 	32
#define MAX_CRC32_SIZE_USED					4


#define MAX_AZURE_CONNSTRING_STORED_INV	    MAX_AZURE_HOSTNAME_USED + MAX_AZURE_CON_ID_USED + MAX_AZURE_CON_KEY_USED  // = 140 bytes
#define MAX_ENCRYPTED_SIZE_STORED_INV		MAX_AZURE_CONNSTRING_STORED_INV + MAX_CLOUD_CONNECT_PIN_LEN + MAX_MAC_ADR_LEN
#define MAX_EEPROM_SIZE_STORE_INV	    	200//180 //Total Eeprom space available in Inverter

#define EEPROM_WR_INV_TRANSFER_SIZE			10 //100 must be divisible by this number

#if (MAX_AZURE_HOSTNAME_USED + MAX_AZURE_CON_ID_USED + MAX_AZURE_CON_KEY_USED + MAX_CLOUD_CONNECT_PIN_LEN + MAX_SHA256_SIZE_USED + MAX_CRC32_SIZE_USED + MAX_MAC_ADR_LEN) != (MAX_EEPROM_SIZE_STORE_INV - 4)
#error "Mismatch of stored bytes in Inverter!!!"
#endif

#if ( MAX_AZURE_HOSTNAME_USED + MAX_AZURE_CON_ID_USED + MAX_AZURE_CON_KEY_USED + MAX_MAC_ADR_LEN + MAX_CLOUD_CONNECT_PIN_LEN ) != ( ( ( MAX_AZURE_HOSTNAME_USED + MAX_AZURE_CON_ID_USED + MAX_AZURE_CON_KEY_USED + MAX_MAC_ADR_LEN + MAX_CLOUD_CONNECT_PIN_LEN  + 15 ) / 16 ) * 16 )
#error "Encrypted bytes stored in Inverter must be divisible by 16!!!"
#endif


#define MAX_WEBSOCKET_CON_KEY				64  + 1 //For '\0'

#define MAX_FIRMWARE_WEB_ADDRESS_LEN		128 + 1 //For '\0'
#define MAX_FIRMWARE_PORT_NUMBER_LEN		5   + 1 //For '\0'
#define MAX_FIRMWARE_CODE_LEN				128 + 1 //For '\0'
#define MAX_BLOB_UPLOAD_CODE_LEN			128 + 1 //For '\0'

#define SHA256_BYTE_SIZE					32
#define AES_KEYLEN							32  //256 bits
#define NUMBER_OF_CALIB_POINTS				3
#define ERROR_LOG_SIZE						10  //Number of data sectors for error log
#define NUMBER_OF_INPUTS					8
#define NUMBER_OF_OUTPUTS					8
#define NUMBER_OF_INV_INPUTS				4
#define NUMBER_OF_INV_OUTPUTS				4
#define MAX_NUMBER_OF_INVERTER_SLAVES		6
#define PRODUCT_NAME_MAX_LEN				30

#define configMAC_ADDR_LEN                  20

typedef struct __attribute__((__packed__)) {
    uint16_t x;
    uint16_t y;
} _TSC2046_Cal_Points;

enum{
	E_STRING,
	E_BYTES,
	E_BYTES_IP,
	E_UINT16,
	E_INT16,
	E_UINT32,
	E_UINT8,
	E_INT8,
	E_RTC = 8,
	E_BYTES_PIN,
	E_INT32,
	E_NONE,
};


typedef struct __attribute__((__packed__)) {
  _TSC2046_Cal_Points P[NUMBER_OF_CALIB_POINTS];
  int16_t			  xOffset;
  int16_t			  yOffset;
  uint8_t 		      Sha256Chk[32];
} TSC2046_Calibration_PointsType;

typedef struct _snvs_hp_rtc_datetime
{
    uint16_t year;  /*!< Range from 1970 to 2099.*/
    uint8_t month;  /*!< Range from 1 to 12.*/
    uint8_t day;    /*!< Range from 1 to 31 (depending on month).*/
    uint8_t hour;   /*!< Range from 0 to 23.*/
    uint8_t minute; /*!< Range from 0 to 59.*/
    uint8_t second; /*!< Range from 0 to 59.*/
} snvs_hp_rtc_datetime_t;


typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[200]; //Make this smaller according to extra space occupied in AppNotChangedSetValsEepromType;
}InsertedSpace1Type;

typedef struct  __attribute__((__packed__)) {
	uint8_t					AppSerialNo[MAX_SERIAL_NO_LEN];
	uint8_t					AppPcbSerialNo[MAX_PCB_SERIAL_NO_LEN];

	uint32_t				InvSerialNumber;

	uint8_t					AppFirmwareUpgradeWebAddress[MAX_FIRMWARE_WEB_ADDRESS_LEN];
	uint8_t					AppFirmwareUpgradePortNumber[MAX_FIRMWARE_PORT_NUMBER_LEN];
	uint8_t					AppFirmwareUpgradeCode[MAX_FIRMWARE_CODE_LEN];

	uint8_t					AppPrimary1AzureConnectionString[MAX_AZURE_CONNECTION_STRING + 4 ]; //Because of CBC Encryption it must be a multiple of 16
	uint8_t					AppPrimary2AzureConnectionString[MAX_AZURE_CONNECTION_STRING - 4 ];

	uint8_t					AppWebsocketConnectionKey[MAX_WEBSOCKET_CON_KEY];

	snvs_hp_rtc_datetime_t	InstallationTime;

	uint16_t				AppUseCloudConnect;
	union{
		uint8_t				AppCloudConnectPinCode[ MAX_CLOUD_CONNECT_PIN_LEN ];
		uint32_t			AppCloudConnectPinCodeU32;
	};

	uint8_t					AppBlobUploadCode[MAX_BLOB_UPLOAD_CODE_LEN];

	uint8_t					AppAes256DecryptionKey[ AES_KEYLEN ];
	uint8_t					AppMacAddress[ configMAC_ADDR_LEN ];

	uint8_t 				Sha256Chk[ SHA256_BYTE_SIZE ];
}AppRarelyChangedSetValsEepromType;


typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[6]; //Make this smaller according to extra space occupied in AppNotChangedSetValsEepromType;
}InsertedSpace2Type;

typedef struct  __attribute__((__packed__)) {
	uint32_t 	AppSelectedRunPressure;
	uint32_t	AppStandardPressure;
	uint32_t	AppHighPressure;
	uint32_t	AppLowPressure;
	uint32_t	AppUserPressure;

	uint32_t	AppPostRunTime;
	uint32_t	AppDryRunLevel;
	uint32_t	AppAccellerationRamp;

	uint32_t 	AppStartUpMethod;
	uint32_t 	AppStartUpMethodPressVal;
	uint32_t 	AppQuickstartLevel;
	uint32_t 	AppQuickstartLevelVal;
	uint32_t 	AppAutoOffDelay;
	uint32_t 	AppAutoOffDelayVal;
	uint32_t 	AppSelectedLanguage;

	uint32_t    AppSetAllowNoInlet;
	uint32_t    AppDelayedStart;
	uint32_t    AppDelayedStartTime;
	uint32_t    AppLowLevelAlarmTime;
	uint32_t    AppScreenSaverTime;
	uint32_t    AppScreenSaverType;

	uint32_t 	AppUnitType;
	uint16_t 	AppBoosterType;
	uint16_t	AppBrand;

	XBool   	AppAutoIpAddress;
	uint8_t		AppIpAddress[MAX_IP_ADDRESS_LEN];
	uint8_t		AppSubnetMask[MAX_SUBNET_ADDRESS_LEN];
	uint8_t		AppGateway[MAX_GATEWAY_ADDRESS_LEN];
	uint8_t		AppPrimaryDnsIpAddress[MAX_IP_ADDRESS_LEN];
	uint8_t		AppSecondaryDnsIpAddress[MAX_IP_ADDRESS_LEN];
	uint8_t		whichDnsInUse;

	uint8_t		NOT_USED_AppMacAddress[configMAC_ADDR_LEN];

	uint8_t		SntpTimeSetRtcOn;
	int8_t		HourOffsetFromUTC;
	uint8_t		UseDaylightSavingTimeOn;
	uint8_t		SntpServerAddress[MAX_SNTP_SERVER_ADDRESS_LEN];

	uint16_t	booster5kW;
	uint16_t	FoamaticType;

	uint8_t		WashProgramPin[ FOAMATIC_WASH_PROGRAM_PIN_LEN ];
	uint16_t	MaxPauseTime;

	uint16_t    DACScale;

	uint8_t		InvModbusSlaveId;
	uint8_t		InvModbusSlavesOnBus;
	uint8_t		OtherModbusSlaveId;
	uint8_t		OtherModbusSlavesOnBus;

	uint16_t    InternalDACScale;
	uint16_t    FlowDetectDelay;
	uint8_t     Flowdetectactive;

	uint16_t	AreaValveFeedbackTime;


	uint8_t     LockHourStart;
	uint8_t     LockMinStart;
	uint8_t     LockHourEnd;
	uint8_t     LockMinEnd;
	uint8_t     LockDays;
	uint8_t     SessionHourStart;
	uint8_t     SessionMinStart;
	uint8_t     SessionHourEnd;
	uint8_t     SessionMinEnd;

	uint16_t    FlowSensorMinFlow;
	uint16_t    FlowSensorMaxFlow;
	uint8_t     FlowSensorMaxSignal;
	uint8_t     FlowSensorMinSignal;

	union{
			uint32_t	AzureAuthenticateCode;
			uint8_t	    AzureAuthenticateCodeBytes[ 4 ];
	};

	uint8_t     AppReadAdcIndex;

	uint16_t    ProgramFinishedTime;

	uint8_t		ProductName1[ PRODUCT_NAME_MAX_LEN ];
	uint8_t		ProductName2[ PRODUCT_NAME_MAX_LEN ];
	uint8_t		ProductName3[ PRODUCT_NAME_MAX_LEN ];


	uint16_t	InvPresSensor1;
	uint16_t	InvPresSensor2;
	uint16_t	InvPresSensor3;
	int32_t		DryRunLevelDelta;
	int32_t		DryRunSensorLoadLow;
	int32_t		DryRunLowSensorSignal;

	uint16_t	CompressorStartLevel;
	int16_t 	P3LowSensorSignal;
	uint16_t 	ParamUpdated;

	uint8_t 	Sha256Chk[ SHA256_BYTE_SIZE ];
}AppSettingValsEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[20]; //Make this smaller according to extra space occupied in AppSettingValsEepromType;
}InsertedSpace3Type;

typedef struct  __attribute__((__packed__)) {
	snvs_hp_rtc_datetime_t	LastLogTime;
	uint32_t 			    TotalkWh[ MAX_NUMBER_OF_INVERTER_SLAVES ];
	uint32_t 				ToTalOnHours[ MAX_NUMBER_OF_INVERTER_SLAVES ];
	uint32_t 				ToTalRunHours[ MAX_NUMBER_OF_INVERTER_SLAVES ];
	uint32_t 				TripkWh[ MAX_NUMBER_OF_INVERTER_SLAVES ];
	uint32_t 				TripOnHours;
	uint32_t 				TripRunHours[ MAX_NUMBER_OF_INVERTER_SLAVES ];
	snvs_hp_rtc_datetime_t	ResetTripTime;

	uint8_t					dummy;
	uint32_t				TripHoursCompressor;  	//This value is stored in seconds and therefore it should be divided by 3600 to get hours!
	uint32_t				TotalHoursCompressor;	//This value is stored in seconds and therefore it should be divided by 3600 to get hours!
	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[4];
	}Crc32Check;
}AppCountersEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[80]; //Make this smaller according to extra space occupied in AppCountersEepromType;
}InsertedSpace4Type;


typedef struct  __attribute__((__packed__)) {
	uint16_t 	last_in;
	uint16_t	size;
	uint16_t	used;
	uint32_t	checkCRC32;
	uint8_t 	notUsed_Sha256Chk[28];
}ErrorLogEepromCtrlSectorType;

typedef struct  __attribute__((__packed__)) {
	ErrorLogEepromDataSectorType ErrorLogEepromDataSectors[ ERROR_LOG_SIZE ];
}ErrorLogEepromAllDataSectorType;


typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[100]; //Make this smaller according to extra space occupied in AppNotChangedSetValsEepromType;
}InsertedSpace5Type;

#define WDOG_TRACE_BUFFER_SIZE 8  // Adjust based on available memory

typedef struct  __attribute__((__packed__)) {
//	snvs_hp_rtc_datetime_t	Time;
	uint32_t 			    TypeFaults;
	uint32_t 			    Time;
	uint32_t 				WdogFaults;
	uint32_t 				WdogFaultAddress;
	uint32_t 				TelemetryDataCount;

	uint32_t				lr;
	uint32_t				sp;

    uint32_t 				ExecutionTrace[ WDOG_TRACE_BUFFER_SIZE ];  // Added trace buffer
    char					TaskName[12];

	uint32_t				Crc32;
}AppWatchdogFaultsEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[3]; //Make this smaller according to extra space occupied in AppNotChangedSetValsEepromType;
}InsertedSpace6Type;


typedef struct  __attribute__((__packed__)) {
	uint32_t 			    MultiInvRuntimesSec[ 6 ];  //Important should be the same as MAX_NUMBER_OF_INVERTER_SLAVES
	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[ 4 ];
	}Crc32Check;
}AppMultiInvRuntimesEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[22]; //Make this smaller according to extra space occupied in AppNotChangedSetValsEepromType;
}InsertedSpace7Type;


#define MAX_NUMBER_OF_USERS		10
#define MAX_USER_NAME_LENGTH	20 //Double up of 15 characters because strings from GUI is in Unicode 16bits format
//This struct must not be larger than 128 bytes, because of a limitation in Eeprom read/write functions. Size now = 48 bytes
typedef struct  __attribute__((__packed__)) {
	uint8_t 				userName[ MAX_USER_NAME_LENGTH + 1 ];
	uint8_t 				userDefPres;
	uint8_t 				userThreeStep;
	uint8_t 				userSelPresStep;
	uint8_t				 	userPressure1;
	uint8_t 				userPressure2;
	uint8_t 				userPressure3;
	uint8_t 				userLanguage;
	uint8_t 				userRole;
	uint32_t  				userPin1;
	uint32_t			    userPin2;
	uint32_t			    userUnit;
	uint16_t 				AllowUserMenus;
	uint32_t 				UserScreenSaverTime;
	uint16_t 				UserScreenSaverType;
	uint16_t 				userUpdateTimesIndex;
}AppOneUserSettingsType;

typedef struct  __attribute__((__packed__)) {
	AppOneUserSettingsType	AppUserSettingsTypeVal[ MAX_NUMBER_OF_USERS ];
	uint8_t 				Sha256Chk[ SHA256_BYTE_SIZE ];
}AppUserSettingsTypes;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[130]; //Make this smaller according to extra space occupied in AppUserSettingsTypes;
}InsertedSpace8Type;


typedef struct  __attribute__((__packed__)) {
	uint16_t 			    InputFunctions[ NUMBER_OF_INPUTS ];
	uint16_t 			    InputParameters[ NUMBER_OF_INPUTS ];
	uint16_t 			    OutputFunctions[ NUMBER_OF_OUTPUTS ];
	uint16_t 			    OutputParameters[ NUMBER_OF_OUTPUTS ];


	struct{
		uint16_t			PortMaxCurrent;
		uint16_t 			PortMinCurrent;
	}OutputPortsMinMaxCurrents[ NUMBER_OF_OUTPUTS ];
	uint16_t				PortCurrentDetectTime;

	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[4];
	}Crc32Check;
}AppIOSettingsEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[64]; //Added to make EepromMemoryMapType at least 128 bytes longer
}InsertedSpace9Type;


typedef struct  __attribute__((__packed__)) {
	char					StoredDirName[12];
	char					StoredFileName[64];

	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[4];
	}Crc32Check;
}AppMachineVarsEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[200]; //Added to make EepromMemoryMapType at least 128 bytes longer
}InsertedSpace10Type;

#define APP_PERFORMANCE_DAYS 6
typedef struct  __attribute__((__packed__)) {
	struct{
		uint16_t				RunTime;
		uint16_t				WaterTempMax;
		uint16_t				WaterTempAvg;
		uint16_t				WaterTempMin;
		uint16_t				Power;
	}Days[ APP_PERFORMANCE_DAYS ];

	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[4];
	}Crc32Check;
}App6DaysPerformanceDataEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[200]; //Added to make EepromMemoryMapType at least 128 bytes longer
}InsertedSpace11Type;

typedef struct  {//__attribute__((__packed__)) {
	uint16_t 			    InputFunctions[ NUMBER_OF_INV_INPUTS ];
	uint16_t 			    OutputFunctions[ NUMBER_OF_INV_OUTPUTS ];

	union{
		uint32_t			Crc32;
		uint8_t				Crc32Bytes[4];
	}Crc32Check;
}AppInverterIOSettingsEepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[62]; //Added to make EepromMemoryMapType at least 128 bytes longer
}InsertedSpace12Type;


typedef struct  __attribute__((__packed__)) {
	//Inverter related
	int32_t 	SensorFlowMax;			//def 23884    >40000  0<
	int32_t 	SensorFlowMin;  		//def 0			>40000 0<
	int32_t 	SensorFlowMaxSignal;	//def 500		>1000 0<
	int32_t 	SensorFlowMinSignal;	//def 0         >1000 0<
	float 		SensorFlowADC2Volt;		//def 0.25968
	uint16_t	SensorStartFlow;

	//Display related
	uint16_t    FlowSensorMinFlow;
	uint16_t    FlowSensorMaxFlow;
	uint8_t     FlowSensorMaxSignal;
	uint8_t     FlowSensorMinSignal;
	float		AdcConvertVal;
	float		AdcConvertValIO;

	uint16_t	SAOffPressure;

	uint8_t 	Sha256Chk[ SHA256_BYTE_SIZE ];
}AppSettingVals2EepromType;

typedef struct  __attribute__((__packed__)) {
	uint8_t	EmptySpace[20]; //Added to make EepromMemoryMapType at least 128 bytes longer
}LastInsertedSpaceType;


typedef struct  __attribute__((__packed__)) {
	TSC2046_Calibration_PointsType			mem0;   //Len = 60
	InsertedSpace1Type						mem1;   //Len = 200
	AppRarelyChangedSetValsEepromType  		mem2;
	InsertedSpace2Type						mem3;
	AppSettingValsEepromType   				mem4;
	InsertedSpace3Type						mem5;
	AppCountersEepromType					mem6;
	InsertedSpace4Type						mem7;
	ErrorLogEepromCtrlSectorType			mem8;
	ErrorLogEepromAllDataSectorType			mem9;
	InsertedSpace5Type						mem10;
	AppWatchdogFaultsEepromType				mem11;
	InsertedSpace6Type						mem12;

	AppMultiInvRuntimesEepromType       	mem13;
	InsertedSpace7Type						mem14;

	AppUserSettingsTypes            		mem15;
	InsertedSpace8Type						mem16;
	AppIOSettingsEepromType         		mem17;
	InsertedSpace9Type						mem18;
	AppMachineVarsEepromType           		mem19;
	InsertedSpace10Type						mem20;
	App6DaysPerformanceDataEepromType		mem21;
	InsertedSpace11Type						mem22;
	AppInverterIOSettingsEepromType			mem23;
	InsertedSpace12Type						mem24;
	AppSettingVals2EepromType				mem25;
	LastInsertedSpaceType					mem26;
}EepromMemoryMapType;


#endif /* EEPROMMEMLAYOUT_H_ */
