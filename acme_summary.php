<html>
  <header>
    <title>muc-server-01 generic web server</title>
  </header>
  <body>
    <h1>ACME MyApp1 EPG dashboard</h1>
    <p>This page shows a summary of the End Points registered with each EPG</p>

    <?php
        //include the library
        //include "libchart/libchart/classes/libchart.php";
        set_include_path( "/usr/share/pear/" . PATH_SEPARATOR .  get_include_path());
        require 'ezc/Base/ezc_bootstrap.php';

function newPie ($name, $title, $data1, $data2) {
        //new pie chart instance
        $graph = new ezcGraphPieChart();
        $graph->title = $title;
        $graph->legend = false;
        $graph->options->label = "";
        $graph->data['EPG count'] = new ezcGraphArrayDataSet( array(
           'EPs' => $data1,
           '' => $data2 - $data1,
        ));
        $graph->render( 400, 150, "/var/www/html/" . $name . ".svg" );
}

function newBar ($name, $title, $mydata) {
        // New Graph
        $graph = new ezcGraphBarChart();
        $graph->title = $title;
        $graph->legend = false;
        // Add data
        $graph->data['EPG count'] = new ezcGraphArrayDataSet($mydata); 
        $graph->render( 400, 150, "/var/www/html/" . $name . ".svg" );
}

function apic_login() {
  //Authenticate
  $ch = curl_init();
  curl_setopt($ch, CURLOPT_URL,            "http://192.168.0.50/api/aaaLogin.xml" );
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1 );
  curl_setopt($ch, CURLOPT_POST,           1 );
  curl_setopt($ch, CURLOPT_POSTFIELDS,     "<aaaUser name='admin' pwd='C15co123' />" ); 
  curl_setopt($ch, CURLOPT_HTTPHEADER,     array('Content-Type: application/xml')); 

  //Process answer
  $result = curl_exec ($ch);
  $resultinfo = curl_getinfo ($ch);

  //Extract token out of answer
  $p = xml_parser_create();
  xml_parse_into_struct($p, $result, $vals, $index);
  xml_parser_free($p);
  $token = ($vals[1]['attributes']['TOKEN']);
  return $token;

  //Close socket
  ch_close ($ch);  
}

function getEPNumber ($token, $tenant, $anp, $epg) {
  //Get Number of EPs for EPG
  $ch = curl_init();
  curl_setopt($ch, CURLOPT_URL,            "http://192.168.0.50/api/node/mo/uni/tn-" . $tenant . "/ap-" . $anp . "/epg-" . $epg . ".xml?query-target=children&target-subtree-class=fvCEp&rsp-subtree=children&rsp-subtree-class=fvRsVm,fvRsHyper,fvRsCEpToPathEp,fvIp" );
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1 );
  curl_setopt($ch, CURLOPT_POST,           0 );
  curl_setopt($ch, CURLOPT_HTTPHEADER,     array(
      'Content-Type: application/xml',
      'Cookie: APIC-cookie='.$token
      ));
  //Send GET request
  $result = curl_exec ($ch);

  //Extract token out of answer
  $p = xml_parser_create();
  xml_parse_into_struct($p, $result, $vals, $index);
  xml_parser_free($p);

  // Get the individual IP addresses into an array
  $my_ips = array ();
  foreach ($index['FVIP'] as $ipindex) {
    array_push ($my_ips, $vals[$ipindex]['attributes']['ADDR']);
  }

  // Return the array with the IPs
  //return $vals[0]['attributes']['TOTALCOUNT'];
  return $my_ips;
}

function printIPs ($ip_addresses, $width) {
    // Print the EPs' IP addresses in a new table cell
    print "<td width='" . $width . "'><ul>";
    foreach ($ip_addresses as $ip) {
        print "<li>" . $ip . "</li>";
    }
    print "</ul></td>";
}

//Max number of EPs in the pie diagrams
$max = 10;

// Initialize and start drawing table
$token = apic_login();
$max = 4;

// PRD
print "<h2>My App 1 - PRD</h2>";
print "<center><table width='70%'><tr>";

// First cell: Web-PRD
$ips_epg1 = getEPNumber ($token, "Acme", "MyApp1-PRD", "Web");
$epg1 = count ($ips_epg1);
newPie ("pie1", "EPs in Web", $epg1, $max);
print "<td width='50%'><img alt='Pie chart'  src='pie1.svg' style='border: 1px solid gray;'/></td>";

$ips_epg2 = getEPNumber ($token, "Acme", "MyApp1-PRD", "DB");
$epg2 = count ($ips_epg2);
newPie ("pie2", "EPs in DB", $epg2, $max);
print "<td width='50%'><img alt='Pie chart'  src='pie2.svg' style='border: 1px solid gray;'/></td></tr>";

// Print the EPs' IP addresses in a new row
print "<tr>";
printIPs ($ips_epg1, "50%");
printIPs ($ips_epg2, "50%");
print "</tr>";

// Finish the table
print " </tr></table></center>";

// TST
print "<h2>My App 1 - TST</h2>";
print "<center><table width='70%'><tr>";

// First cell: Web-PRD
$ips_epg3 = getEPNumber ($token, "Acme", "MyApp1-TST", "Web");
$epg3 = count ($ips_epg3);
newPie ("pie3", "EPs in Web", $epg3, $max);
print "<td width='50%'><img alt='Pie chart'  src='pie3.svg' style='border: 1px solid gray;'/></td>";

$ips_epg4 = getEPNumber ($token, "Acme", "MyApp1-TST", "DB");
$epg4 = count ($ips_epg4);
newPie ("pie4", "EPs in DB", $epg4, $max);
print "<td width='50%'><img alt='Pie chart'  src='pie4.svg' style='border: 1px solid gray;'/></td></tr>";

// Print the EPs' IP addresses in a new row
print "<tr>";
printIPs ($ips_epg3, "50%");
printIPs ($ips_epg4, "50%");
print "</tr>";

// Finish the table
print " </tr></table></center>";

//Create bar graph
$allEPGs = array (
  'PRD-Web' => $epg1,
  'PRD-DB' => $epg2,
  'TST-Web' => $epg3,
  'TST-DB' => $epg4,
);
newBar ("bar", "Summary", $allEPGs);

// Draw bar graph
print "<h2>My App 1 - Overall summary</h2>";
print "
            <center>
              <p>Summary of EPG number across EPGs</p>
                <img alt='Bar chart'  src='bar.svg' style='border: 1px solid gray;'/>
            </center>
";
?>

  </body>
</html>
