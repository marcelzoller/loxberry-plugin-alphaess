#!/usr/bin/perl

# Einbinden von Module
use CGI;
use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use IO::Socket::INET;
use LWP::Simple;
use Net::Ping;
use Date::Parse;
use Time::Local;
use Digest::MD5 qw(md5_hex);
use JSON;
use Data::Dumper;
#use Crypt::Mode::CBC;
#use Crypt::OpenSSL::AES;

print "Content-type: text/html\n\n";

# Konfig auslesen
my %pcfg;
my %miniservers;
tie %pcfg, "Config::Simple", "$lbpconfigdir/pluginconfig.cfg";
$UDP_Port = %pcfg{'MAIN.UDP_Port'};
$UDP_Send_Enable = %pcfg{'MAIN.UDP_Send_Enable'};
$HTTP_TEXT_Send_Enable = %pcfg{'MAIN.HTTP_TEXT_Send_Enable'};
$MINISERVER = %pcfg{'MAIN.MINISERVER'};
%miniservers = LoxBerry::System::get_miniservers();
my $Token = %pcfg{'MAIN.TOKEN'};


# Variabel from Alpha ESS Result
my $Ppv1; # PV1 Watt
my $Ppv2; # PV2 Watt
my $Upv1; # PV1 Volt
my $Upv2; # PV2 Volt
my $SoC; # Batterie %
my $Ua; # Grid Volt L1
my $Ub; # Grid Volt L2
my $Uc; # Grid Volt L3
my $Fac; # Grid Frequenz
my $Tinv; # Inverter Temperatur
my $InvWorkMode; # Inverter Status
my $Batv; # Batterie Volt
my $BatC1; # Batterie 1 Current
my $BatC2; # Batterie 2 Current
my $BatC3; # Batterie 3 Current
my $BatC4; # Batterie 4 Current
my $BatC5; # Batterie 5 Current
my $BatC6; # Batterie 6 Current
my $ErrInv; # Error Invertor
my $ErrEms; # Error EMS
my $ErrMeter; # Error Meter
my $ErrBms; # Error BMS 
my $ErrBackupBox; # Error BackupBox 

# Miniserver konfig auslesen
#print "\n".substr($MINISERVER, 10, length($MINISERVER))."\n";
$i = substr($MINISERVER, 10, length($MINISERVER));
$LOX_Name = $miniservers{$i}{Name};
$LOX_IP = $miniservers{$i}{IPAddress};
$LOX_User = $miniservers{$i}{Admin};
$LOX_PW = $miniservers{$i}{Pass};

print "Miniserver\@".$LOX_Name."<br>";
#print $LOX_IP."<br>";
#print $LOX_User."<br>";
#print $LOX_PW."<br>";


# Create my logging object
my $log = LoxBerry::Log->new ( 
	name => 'cronjob',
	filename => "$lbplogdir/vzug.log",
	append => 1
	);
LOGSTART "ALPHA ESS cronjob start";

# UDP-Port Erstellen für Loxone
my $sock = new IO::Socket::INET(PeerAddr => $LOX_IP,
                PeerPort => $UDP_Port,
                Proto => 'udp', Timeout => 1) or die('Error opening socket.');
			

# Loxone HA-Miniserver by Marcel Zoller	
if($LOX_Name eq "lxZoller1"){
	# Loxone Minisever ping test
	LOGOK " Loxone Zoller HA-Miniserver";
	#$LOX_IP="172.16.200.7"; #Testvariable
	#$LOX_IP='172.16.200.6'; #Testvariable
	$p = Net::Ping->new();
	$p->port_number("80");
	if ($p->ping($LOX_IP,2)) {
				LOGOK "Ping Loxone: Miniserver1 is online.";
				LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
			} else{ 
				LOGALERT "Ping Loxone: Miniserver1 not online!";
				LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
				$p->close();
				
				$p = Net::Ping->new();
				$p->port_number("80");
				$LOX_IP = $miniservers{2}{IPAddress};
				$LOX_User = $miniservers{2}{Admin};
				$LOX_PW = $miniservers{2}{Pass};
				#$LOX_IP="172.16.200.6"; #Testvariable
				if ($p->ping($LOX_IP,2)) {
					LOGOK "Ping Loxone: Miniserver2 is online.";
					LOGOK "Ping Loxone: $p->ping($LOX_IP)";
				} else {
					LOGALERT "Ping Loxone: Miniserver2 not online!";
					LOGDEB "Ping Loxone: $p->ping($LOX_IP)";
					#Failback Variablen !!!
					$LOX_IP = $miniservers{1}{IPAddress};
					$LOX_User = $miniservers{1}{Admin};
					$LOX_PW = $miniservers{1}{Pass};	
				} 
			}
		$p->close();			
}			

LOGDEB "Loxone Name: $LOX_Name";			
$username = %pcfg{'MAIN.USERNAME'};
LOGDEB "Username: $username";
$password = %pcfg{'MAIN.PASSWORD'};
LOGDEB "Password: $password";
$sn = %pcfg{'MAIN.SN'};
LOGDEB "SN: $sn";
$api_account = %pcfg{'MAIN.API_ACCOUNT'};
# LOGDEB "API Account: $api_account";
$secretkey = %pcfg{'MAIN.SECRETKEY'};
# LOGDEB "Secretkey: $secretkey";



# ================== Ab hier kommt der Alpha ESS CODE by MZO ==========================
# ====================== Alpha ESS API Spezifkation V2.1  =============================
my $timestamp = time;	# or any other epoch timestamp
my $time = localtime();
LOGDEB "Epoch (UTC) timestamp: $timestamp";
LOGDEB "UTC Time: $time";
# print "TIME\@".$utctime."<br>";
# print "TIME\@".localtime()."<br>";
	

# mein Password verschlüsselt AES256
my $cryptPW = "F5CR9UKsr/7HuVXMwAjkCw==";

 
#my $key = $username; # length has to be valid key size for this cipher
#my $iv = $usernmae;  # 16 bytes
#my $cbc = Crypt::Mode::CBC->new('AES');
#my $ciphertext = $cbc->encrypt($password, $key, $iv);	
##print "AES256 is ". $ciphertext. "<br>";	


# =============  ALPHA ESS LOGIN TOKEN ABHOLDEN - 90 Min gültig =======================
my $strLogin = "api_account=".$api_account."password=".$cryptPW."secretkey=".$secretkey."timestamp=".$timestamp."username=".$username;
#print $strLogin."<br>";
	
# MF5 Hash für Signiere erstellen
my $md5Hash = md5_hex($strLogin);
# print $md5Hash."<br>";
LOGDEB "md5Hash: $md5Hash";

# JSON erstellen für Login Abfrage
my %rec_hash =  ('api_account' => $api_account , 'timestamp' => $timestamp ,'sign' => $md5Hash , 'username' => $username , 'password' => $cryptPW);
my $json = encode_json \%rec_hash;
# print $json ."<br>";
LOGDEB "json: $json";

# Alpha ESS Login Token abholen
my $url = "http://api.alphaess.com/ras/v2/Login";
LOGOK "URL: $url";
my $req = HTTP::Request->new( 'POST', $url );
$req->header( 'Content-Type' => 'application/json' );
$req->content( $json );

my $lwp = LWP::UserAgent->new;
$lwp->request( $req );


# HTTP Request Error handling
my $resp = $lwp->request($req);
if ( $resp->is_success ) {
    my $message = $resp->decoded_content;
	LOGDEB "Received reply: $message";
    #print "Received reply: $message<br>";
	
	$json = decode_json($message);
	#print Dumper($json) ."<br>";
	LOGDEB "Received json: $Dumper($json)";

	
	if ($json->{ReturnCode}== 0){
			LOGOK "Alpha ESS Login erfolgreich. Tokern erhalten:  $json->{Token}";
			$Token = $json->{Token};
			#print "Token: $Token<br>";
			LOGDEB "Token: $Token";
			#print "ReturnCode: $json->{ReturnCode}<br>";
	}  else {
			LOGALERT "ReturnCode: $json->{ReturnCode}";
			#print "ReturnCode: $json->{ReturnCode}<br>";
		}
} else {
	LOGALERT "Alpha ESS Login fehlgeschlagen!";
}

# =============  ALPHA ESS ABFRGAE - GetRunningData =======================
LOGOK "ALPHA ESS Abferage - GetRunningData";
my $strLogin = "api_account=".$api_account."secretkey=".$secretkey."Sn=".$SN."timestamp=".$timestamp."Token=".$Token;
# print $strLogin."<br>";

	
# MF5 Hash für Signiere erstellen
my $md5Hash = md5_hex($strLogin);
# print $md5Hash."<br>";
LOGDEB "md5Hash: $md5Hash"; 

# JSON erstellen für Login Abfrage
my %rec_hash =  ('api_account' => $api_account , 'timestamp' => $timestamp ,'sign' => $md5Hash , 'Token' => $Token , 'Sn' => $SN);

my $json = encode_json \%rec_hash;
# print $json ."<br>";
LOGDEB "json: $json";

# Alpha ESS Login Token abholen
my $url = "http://api.alphaess.com/ras/v2/GetRunningData";
LOGOK "URL: $url";
my $req = HTTP::Request->new( 'POST', $url );
$req->header( 'Content-Type' => 'application/json' );
$req->content( $json );

my $lwp = LWP::UserAgent->new;
$lwp->request( $req );


# HTTP Request Error handling
my $resp = $lwp->request($req);
if ( $resp->is_success ) {
    my $message = $resp->decoded_content;
	LOGDEB "Received reply: $message";
    #print "Received reply: $message<br>";
	
	$json = decode_json($message);
	#print Dumper($json) ."<br>";
	LOGDEB "Received json: $Dumper($json)";
	
	if ($json->{ReturnCode}== 0){
			LOGOK "Alpha ESS Abfrage erfolgreich - GetRunningData";
			my @result = @{$json->{Result}};
			foreach my $f ( @result ) {
				
				
				$Ppv1 = $f->{Ppv1}; # PV1 Watt
				$Ppv2= $f->{Ppv2}; # PV2 Watt
				$Upv1= $f->{Upv1}; # PV1 Volt
				$Upv2= $f->{Upv2}; # PV2 Volt
				$SoC= $f->{Soc}; # Batterie SOC%
				$Ua= $f->{Ua}; # Grid Volt L1
				$Ub= $f->{Ub}; # Grid Volt L2
				$Uc= $f->{Uc}; # Grid Volt L3
				$Fac= $f->{Fac}; # Grid Frequenz
				$Tinv= $f->{Tinv}; # Inverter Temperatur
				$InvWorkMode= $f->{InvworkMode}; # Inverter Status
				$Batv= $f->{Batv}; # Batterie Volt
				$BatC1= $f->{BatC1}; # Batterie 1 Current
				$BatC2= $f->{BatC2}; # Batterie 2 Current
				$BatC3= $f->{BatC3}; # Batterie 3 Current
				$BatC4= $f->{BatC4}; # Batterie 4 Current
				$BatC5= $f->{BatC5}; # Batterie 5 Current
				$BatC6= $f->{BatC6}; # Batterie 6 Current
				$ErrInv= $f->{ErrInv}; # Error Invertor
				$ErrEms= $f->{ErrEms}; # Error EMS
				$ErrMeter= $f->{ErrMeter}; # Error Meter
				$ErrBms= $f->{ErrBms}; # Error BMS 
				$ErrBackupBox= $f->{ErrBackupBox}; # Error BackupBox 
				
				
				
				print "Ppv1\@$Ppv1  <br>";
				print "Ppv2\@$Ppv2  <br>";	
				print "Upv1\@$Upv1  <br>";	
				print "Upv2\@$Upv2 <br>";					
				print "SoC\@$SoC  <br>";
				print "Ua\@$Ua <br>";
				print "Ub\@$Ub  <br>";
				print "Uc\@$Uc  <br>";
				print "Fac\@$Fac <br>";
				print "Tinv\@$Tinv  <br>";	
				print "InvWorkMode\@$InvWorkMode  <br>";
				print "Batv\@$Batv  <br>";
				print "BatC1\@$BatC1 <br>";
				print "BatC2\@$BatC2 <br>";
				print "BatC3\@$BatC3 <br>";
				print "BatC4\@$BatC4 <br>";
				print "BatC5\@$BatC5 <br>";
				print "BatC6\@$BatC6 <br>";
				print "ErrInv\@$ErrInv  <br>";
				print "ErrEms\@$ErrEms  <br>";
				print "ErrMeter\@$ErrMeter  <br>";
				print "ErrBms\@$ErrBms  <br>";
				print "ErrBackupBox\@$ErrBackupBox  <br>";
				
				
				LOGDEB "Ppv1: $Ppv1";
				LOGDEB "Ppv2: $Ppv2";	
				LOGDEB "Upv1: $Upv1";	
				LOGDEB "Upv2: $Upv2";					
				LOGDEB "SoC: $SoC";
				LOGDEB "Ua: $Ua";
				LOGDEB "Ub: $Ub";
				LOGDEB "Uc: $Uc";
				LOGDEB "Fac: $Fac";
				LOGDEB "Tinv: $Tinv";	
				LOGDEB "InvWorkMode: $InvWorkMode";
				LOGDEB "Batv: $Batv";
				LOGDEB "BatC1: $BatC1";
				LOGDEB "BatC2: $BatC2";
				LOGDEB "BatC3: $BatC3";
				LOGDEB "BatC4: $BatC4";
				LOGDEB "BatC5: $BatC5";
				LOGDEB "BatC6: $BatC6";
				LOGDEB "ErrInv: $ErrInv";
				LOGDEB "ErrEms: $ErrEms";
				LOGDEB "ErrMeter: $ErrMeter";
				LOGDEB "ErrBms: $ErrBms";
			}
			
			# print "ReturnCode: $json->{ReturnCode}<br>";
			LOGDEB "ReturnCode: $json->{ReturnCode}<br>";
	}  else {
			if($json->{ReturnCode}== 1){
				LOGALERT "Alpha ESS: ERROR";
			}
			if($json->{ReturnCode}== 2){
				LOGALERT "Alpha ESS: Required fields not filled";
			}
			if($json->{ReturnCode}== 3){
				LOGALERT "Alpha ESS: Invalide timestamp";
			}
			if($json->{ReturnCode}== 4){
				LOGALERT "Alpha ESS: Authentication unsuccessful ";
			}
			if($json->{ReturnCode}== 5){
				LOGALERT "Alpha ESS: User alredy exist";
			}
			if($json->{ReturnCode}== 6){
				LOGALERT "Alpha ESS: License alredy exist";
			}
			if($json->{ReturnCode}== 7){
				LOGALERT "Alpha ESS: SN alredy exist";
			}
			if($json->{ReturnCode}== 8){
				LOGALERT "Alpha ESS: Invalid API Account";
			}
			if($json->{ReturnCode}== 9){
				LOGALERT "Alpha ESS: Invalid User";
			}
			if($json->{ReturnCode}== 10){
				LOGALERT "Alpha ESS: Emailadess and Username do not match our records.";
			}
			if($json->{ReturnCode}== 11){
				LOGALERT "Alpha ESS: Username or password are incorrect.";
			}
			if($json->{ReturnCode}== 12){
				LOGALERT "Alpha ESS: Invalid SN";
			}
			if($json->{ReturnCode}== 13){
				LOGALERT "Alpha ESS: The commend Dispatch failed ";
			}
			if($json->{ReturnCode}== 14){
				LOGALERT "Alpha ESS: Login timeout Token";
			}
			if($json->{ReturnCode}== 15){
				LOGALERT "Alpha ESS: No persission";
			}
			if($json->{ReturnCode}== 16){
				LOGALERT "Alpha ESS: Abnormal Login";
			}
			if($json->{ReturnCode}== -1){
				LOGALERT "Alpha ESS: Inknoe mistake";
			}
			LOGALERT "ReturnCode: $json->{ReturnCode}";
			#print "ReturnCode: $json->{ReturnCode}<br>";
		}
} else {
	LOGALERT "Alpha ESS Abfrage fehlgeschlagen!";
}


	
if ($HTTP_TEXT_Send_Enable == 1) {
	LOGDEB "Loxone IP: $LOX_IP";
	LOGDEB "User: $LOX_User";
	LOGDEB "Password: $LOX_PW";
	
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Ppv1/$Ppv1"); # PV1 Watt
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Ppv2/$Ppv2"); # PV2 Watt
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Upv1/$Upv1"); # PV1 Volt
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Upv2/$Upv2"); # PV2 Volt
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_SoC/$SoC"); # Batterie %
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Ua/$Ua"); # Grid Volt L1
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Ub/$Ub"); # Grid Volt L2
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Uc/$Uc"); # Grid Volt L3
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Fac/$Fac"); # Grid Frequenz
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Tinv/$Tinv"); # Inverter Temperatur
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_InvWorkMode/$InvWorkMode"); # Inverter Status
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_Batv/$Batv"); # Batterie Volt
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC1/$BatC1"); # Batterie 1 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC2/$BatC2"); # Batterie 2 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC3/$BatC3"); # Batterie 3 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC4/$BatC4"); # Batterie 4 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC5/$BatC5"); # Batterie 5 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_BatC6/$BatC6"); # Batterie 6 Current
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_ErrInv/$ErrInv"); # Error Invertor
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_ErrEms/$ErrEms"); # Error EMS
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_ErrMeter/$ErrMeter"); # Error Meter
	$contents = get("http://$LOX_User:$LOX_PW\@$LOX_IP/dev/sps/io/AlphaESS_ErrBms/$ErrBms"); # Error BMS 
	
	
	}
else {
	LOGDEB "HTTP_TEXT_Send_Enable: 0";
}
	
if ($UDP_Send_Enable == 1) {

	#UDP Sender PORT
	$sock = IO::Socket::INET->new(
		Proto    => 'udp',
		PeerPort => $UDP_Port,
		PeerAddr => $LOX_IP,
	) or do {
		LOGERR "UDP Error: Could not creat socket!!!!!!";
		#LOGEND "Operation finished NOT sucessfully.";
		#Exit 1;
		};
	LOGOK "UDP Socket erfolgreich erstellt.";
	
	
	$UDP_Text = "AlphaESS_Ppv1\@" .$Ppv1;
	$UDP_Text = $UDP_Text . " AlphaESS_Ppv2\@" .$Ppv2;
	$UDP_Text = $UDP_Text . " AlphaESS_Upv1\@" .$Upv1;
	$UDP_Text = $UDP_Text . " AlphaESS_Upv2\@" .$Upv2;
	$UDP_Text = $UDP_Text . " AlphaESS_SoC\@" .$SoC;
	$UDP_Text = $UDP_Text . " AlphaESS_Ua\@" .$Ua;
	$UDP_Text = $UDP_Text . " AlphaESS_Ub\@" .$Ub;
	$UDP_Text = $UDP_Text . " AlphaESS_Uc\@" .$Uc;
	$UDP_Text = $UDP_Text . " AlphaESS_Fac\@" .$Fac;
	$UDP_Text = $UDP_Text . " AlphaESS_Tinv\@" .$Tinv;
	$UDP_Text = $UDP_Text . " AlphaESS_InvWorkMode\@" .$InvWorkMode;
	$UDP_Text = $UDP_Text . " AlphaESS_Batv\@" .$Batv;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC1\@" .$BatC1;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC2\@" .$BatC2;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC3\@" .$BatC3;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC4\@" .$BatC4;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC5\@" .$BatC5;
	$UDP_Text = $UDP_Text . " AlphaESS_BatC5\@" .$BatC6;
	$UDP_Text = $UDP_Text . " AlphaESS_ErrInv\@" .$ErrInv;
	$UDP_Text = $UDP_Text . " AlphaESS_ErrEms/\@" .$ErrEms;
	$UDP_Text = $UDP_Text . " AlphaESS_ErrMeter\@" .$ErrMeter;
	$UDP_Text = $UDP_Text . " AlphaEES_ErrBms\@" .$ErrBMS;
	
	LOGDEB "UDP Text: $UDP_Text";
	$sock->send($UDP_Text) or do {
		LOGERR "UDP Error: send!!!!!!";
		#LOGEND "Operation finished NOT sucessfully.";
		#Exit 1;
		};
	LOGOK "UDP Text erfolgreich gesendet.";
	
	# print $sock "DeviceName1\@$DeviceNameStr\; Serial1\@$SerialStr\; Program1\@$ProgrammStr\; Status1\@$StatusStr\; Time1\@$ZeitStr";
	LOGDEB "Loxone IP: $LOX_IP";
	LOGDEB "UDP Port: $UDP_Port";
	# LOGDEB "UDP Send: DeviceName1\@$DeviceNameStr\; Serial1\@$SerialStr\; Program1\@$ProgrammStr\; Status1\@$StatusStr\; Time1\@$ZeitStr";
	}

# We start the log. It will print and store some metadata like time, version numbers
# LOGSTART "ALPHA ESS cronjob start";
  
# Now we really log, ascending from lowest to highest:
# LOGDEB "This is debugging";                 # Loglevel 7
# LOGINF "Infos in your log";                 # Loglevel 6
# LOGOK "Everything is OK";                   # Loglevel 5
# LOGWARN "Hmmm, seems to be a Warning";      # Loglevel 4
# LOGERR "Error, that's not good";            # Loglevel 3
# LOGCRIT "Critical, no fun";                 # Loglevel 2
# LOGALERT "Alert, ring ring!";               # Loglevel 1
# LOGEMERGE "Emergency, for really really hard issues";   # Loglevel 0
  
LOGEND "Operation finished sucessfully.";
