<html>
  <header>
    <title>muc-server-01 generic web server</title>
  </header>
  <body>
    <h1>EPG dashboard</h1>
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
           '' => $data2,
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
  return $vals[0]['attributes']['TOTALCOUNT'];

  //Close
  ch_close ($ch);

}

//Max number of EPs in the pie diagrams
$max = 10;

$token = apic_login();
$max = 10;
$epg1 = getEPNumber ($token, "Pod1", "Pod1", "EPG1");
newPie ("pie1", "EPs in EPG 1", $epg1, $max);
$epg2 = getEPNumber ($token, "Pod1", "Pod1", "EPG2");
newPie ("pie2", "EPs in EPG 2", $epg2, $max);

//Create bar graph
$allEPGs = array (
  'EPG1' => $epg1,
  'EPG2' => $epg2,
);
newBar ("bar", "Summary", $allEPGs)  

?>

	    <table width='100%'>
	      <tr>
		  <td width='33%'><img alt='Pie chart'  src='pie1.svg' style='border: 1px solid gray;'/></td>
		  <td width='33%'><img alt='Pie chart'  src='pie2.svg' style='border: 1px solid gray;'/></td>
	      </tr>
	    </table>

            <center>
              <p>Summary of EPG number across EPGs</p>
                <img alt='Bar chart'  src='bar.svg' style='border: 1px solid gray;'/>
            </center>

  </body>
</html>
