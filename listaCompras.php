<?php
	session_start();
?>

<html>
  <head>
    <title>Stock :: Menu Principal</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <link rel="stylesheet" type="text/css" href="estilos.css">
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link href="css2/bootstrap.min.css" rel="stylesheet">
    <link href="css2/style.css" rel="stylesheet">
  </head>

	<body>
		<br><br>
		<div class="container-fluid">
      <div class="row">
        <div class="col-md-4">
        </div>
        <div class="col-md-4">
        <button onclick="window.location.href='menu.php'" class="btn btn-block btn-lg btn-outline-success">Voltar ao Menu</button><br><br>
        <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=novalistacompra'"> Gerar Lista</button><br>

        <?php if($_SESSION['permissao'] == 'admin'){ ?>
        <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="alert('em breve!');"> Lista Atual</button><br>
        <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="alert('em breve!');"> Listas Anteriores</button><br>
        <?php } ?>
        </div>
        <div class="col-md-4">
        </div>
      </div>
		</div>

		<script src="js/jquery.min.js"></script>
		<script src="js/bootstrap.min.js"></script>
		<script src="js/scripts.js"></script>

  </body>
</html>
