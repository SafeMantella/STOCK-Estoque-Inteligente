<?php
  session_start();
?>

<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <link rel="stylesheet" type="text/css" href="estilos.css">
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="css2/bootstrap.min.css" rel="stylesheet">
    <link href="css2/style.css" rel="stylesheet">
</head>

  <body>
    <?php	
      if(isset($_SESSION['cod_usuario'])){
        session_destroy();
    ?>  <script>alert("Tchau!");</script>
    <?php
        header("Refresh:0; url=menu.php");
      }
    ?>
  </body>
</html>
