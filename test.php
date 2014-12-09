<?php

$dbconn = pg_connect("dbname=dong_eq")
	or die('Could not connect: '. pg_last_error());

?>