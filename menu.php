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
    <?php
	    if(isset($_SESSION['cod_usuario']))
	    {
		?>
		<br><br>
		<div class="container-fluid">
      <div class="row">
        <div class="col-md-4">
        </div>
        <div class="col-md-4">
          <?php
            echo "<h3>Olá ".$_SESSION['nome']."!</h3><br><h3>Bem vindo ao sistema Stock!</h3><br>";
            echo "<label>Código de seu estoque: ".$_SESSION['cod_estoque']."</label>";
          ?>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=listarUsuariosLocal'"><img style="width:30px; float:left;" src="lista.jpg"> Usuários em seu estoque</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=listaritem'"><img style="width:30px; float:left;" src="lista.jpg"> Listar Itens</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='buscarItem.html'"><img style="width:30px; float:left;" src="buscar.jpg"> Buscar Itens</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=acessaestoque'"><img style="width:30px; float:left;" src="adc.jpg"> Meu Estoque</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='listaCompras.php'"><img style="width:30px; float:left;" src="listacomp.jpg"> Lista de Compras</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='quemSomos.html'"><img style="width:30px; height: 30px; float:left;" src="qmsomos.jpg"> Quem Somos?</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='manual.html'"> Como o sistema funciona?</button><br>

          <?php 
            if($_SESSION['permissao'] == 'admin'){ 
          ?>
          <br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='cadastroDispensa.html'"> Cadastrar Estoque - DEV</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=listarestoques'"> Listar Estoques - DEV</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='cadastroitem.html'"> Cadastrar Novo Item - DEV</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='cadastroUsuario.html'"> Cadastrar Usuários - DEV</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='processa.php?acao=listarUsuarios'"> Listar Usuários - DEV</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='buscarUsuario.html'"> Buscar Usuários - DEV</button><br>
          <br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="alert('em breve');"> SAC</button><br>
          <br>
          <?php 
            } 
          ?>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='saida.php'"><img style="width:30px; float:left;" src="sair.jpg"> Sair</button><br>

        </div>
        <div class="col-md-4">
        </div>
      </div>
		</div>

		<script src="js/jquery.min.js"></script>
		<script src="js/bootstrap.min.js"></script>
		<script src="js/scripts.js"></script>
    
    <?php
      }else{
		?>
		<br><br>
		<div class="container-fluid">
      <div class="row">
        <div class="col-md-4">
        </div>
        <div class="col-md-4">
          <h3>Bem-vindo ao STOCK!</h3><br><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='login.html'"> Login</button><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='verifica_cadastro.html'"> Cadastre-se</button><br>
          <br><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="window.location.href='quemSomos.html'">Quem Somos?</button><br><br>
          <button type="button" class="btn btn-block btn-lg btn-outline-success" onclick="alert('em breve');"> SAC</button><br>
        </div>
        <div class="col-md-4">
        </div>
      </div>
		</div>

		<script src="js/jquery.min.js"></script>
		<script src="js/bootstrap.min.js"></script>
		<script src="js/scripts.js"></script>
		<?php
	    }
    ?>
  </body>
</html>
