<?php
	include_once "config.php";
	include_once "connection.php";
	session_start();
	$conexao = new Connection($host, $user, $password, $database);
?>

<html>
  <head>
    <title></title>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="css4/bootstrap.min.css" rel="stylesheet">
    <link href="css4/style.css" rel="stylesheet">
  </head>

<body>
	<div class="container-fluid">
	<div class="row">
	<div class="col-md-3">
	</div>
	<div class="col-md-6">
  <?php
    if($_SERVER['HTTP_REFERER'] === $url.'login.html'){
      $email = $_POST['email'];
      $senha = $_POST['senha'];
      $senha = sha1($senha);

      if( (empty($email) == TRUE) || (empty($senha) == TRUE) ){
        header("Refresh: 0; url=login.php"); // se não funcionar, fechar e abrir tag PHP antes dessa linha
  ?>    <script>alert("Você deve preencher todos os campos corretamente!");</script>
  <?php
		    exit(0);
		  }else{

        $sql = "SELECT * FROM usuario WHERE email = '$email'";
        $conexao->query($sql);

        if($conexao->num_rows() > 0){
          $sql = "SELECT cod_estoque, permissao, cod_usuario, nome AS n FROM usuario WHERE email = '$email' AND senha = '$senha'";
          $conexao->query($sql);

          if($conexao->num_rows() > 0){
            $tupla = $conexao->fetch_assoc();
            $cod_usuario = $tupla['cod_usuario'];
            $cod_estoque = $tupla['cod_estoque'];
            $nome = $tupla['n'];
            $permissao = $tupla['permissao'];

            $_SESSION['cod_usuario'] = $cod_usuario;
            $_SESSION['cod_estoque'] = $cod_estoque;
            $_SESSION['nome'] = $nome;
            $_SESSION['permissao'] = $permissao;
          
            header("Refresh: 0; url=menu.php");
            
            exit(0);
          }else{
            header("Refresh: 0; url=login.html");
  ?>        <script>alert("Email ou Senha Incorretos");</script>
  <?php
            exit(0);
          }
        }
      }
	  }else{
      if($_SERVER['HTTP_REFERER'] === $url.'cadastroUsuario.html'){
        $email = $_POST['email'];
        $senha = $_POST['senha'];
        $confirmarSenha = $_POST['confirmarSenha'];
        $nome = $_POST['nome'];
        $cod_estoque = $_POST['cod_estoque'];
        $permissao = $_POST['permissao'];//usuario ou admin SEMPRE

        if( (empty($permissao) == TRUE) || (empty($senha) == TRUE) || (empty($nome) == TRUE) || (empty($email) == TRUE) || (empty($confirmarSenha) == TRUE) || (empty($cod_estoque) == TRUE)){
          header("Refresh: 0; url=cadastroUsuario.html");
  ?>      <script>alert("Você deve preencher todos os campos corretamente!");</script>
  <?php
          exit(0);
        }
        if($senha !== $confirmarSenha){
          header("Refresh: 0; url=cadastroUsuario.html");
  ?>      <script>alert("Senhas não correspondem");</script>
  <?php
          exit(0);
        }

        $senha = sha1($senha);
        $sql = "INSERT INTO usuario(nome, email, senha, permissao, cod_estoque) VALUES ('$nome', '$email', '$senha', '$permissao', '$cod_estoque')";
        $status = $conexao->query($sql);

        if($status === TRUE){
  ?>
  <?php
        header("Refresh: 0; url=menu.php");
  ?>    <script>alert("Cadastro feito com sucesso!");</script>
  <?php
        exit(0);
        }
      }else{
        if($_SERVER['HTTP_REFERER'] === $url.'cadastroitem.html'){
          $descricao = $_POST['descricao'];
          $categoria = $_POST['categoria'];
          $sql = "INSERT INTO item(cod_item, descricao, categoria) VALUES (NULL, '$descricao', '$categoria')";
          $status = $conexao->query($sql);

          if($status === TRUE){
  ?>
  <?php
          header("Refresh: 0; url=menu.php");
  ?>      <script>alert("Cadastro feito com sucesso!");</script>
  <?php
          exit(0);
          }
        }else{
          if($_SERVER['HTTP_REFERER'] === $url.'cadastroDispensa.html'){
            $descricao = $_POST['descricao'];
            $sql = "INSERT INTO estoque(cod_estoque, descricao) VALUES (NULL, '$descricao')";
            $status = $conexao->query($sql);

            if($status === TRUE){
              header("Refresh: 0; url=menu.php");
  ?>          <script>alert("Cadastro feito com sucesso!");</script>
  <?php
              exit(0);
            }
          }else{
            if(isset($_GET['acao'])){
              if($_GET['acao'] === 'listarUsuarios'){
                $sql = "SELECT cod_usuario, nome, email, permissao, cod_estoque FROM usuario";
                $conexao->query($sql);

                echo "<br><br>";
                echo "<table class='table table-hover'>";?>
                <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><?php
                $headerFlag = FALSE;

                for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                  echo "<tr class='table-active'>";
                  foreach ($tupla as $key => $value){
                    if($headerFlag === FALSE){
                      echo "<th>$key </th>";
                    }else{
                      echo "<td>$value </td>";
                    }
                  }
                  echo "</tr>";

                  echo "<tr>";
                  if($headerFlag === FALSE){
                    echo "<br>";
                    foreach ($tupla as $key => $value){
                      echo "<td>$value </td>";
                    }
                    $headerFlag = TRUE;
                  }
                  echo "<br>";
                }
                echo "</table>";
              
              }else{

                if($_GET['acao'] === 'listarestoques'){
                  $sql = "SELECT n.cod_estoque AS cod_estoque, n.descricao AS descricao FROM estoque n";
                  $conexao->query($sql);

                  echo "<br><br>";
                  echo "<button onclick=window.location.href='menu.php' class='btn btn-block btn-md btn-outline-success'>Voltar ao Menu</button><br>";
                  echo "<br>";

                  echo "<table class='table table-hover'>";
                  echo "<tr class='table-active'>";
                  echo "<th>ID Estoque</th>";
                  echo "<th>Descrição</th>";
                  echo "</tr>";

                  for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                    echo "<tr>";
                    echo "<td>".$tupla['cod_estoque']."</td> ";
                    echo "<td>".$tupla['descricao']."</td> ";
                    echo "</tr>";
                  }
                  echo "</table>";

                }else{

                  if($_GET['acao'] === 'adicionaItem'){//fazer
                    $cod1 = $_GET['item'];
                    $codest = $_SESSION['cod_estoque'];
                    $qtd_des = $_POST['qtd_desejada'];
                    $qtd_est = $_POST['qtd_estoque'];

                    if($qtd_des == "" || $qtd_des == "" || $qtd_des <= 0 || $qtd_est <= 0){
                      header("Refresh: 0; url=processa.php?acao=listaritem");
  ?>                  <script>alert("erro, preencha os campos corretamente");</script>
  <?php
                    }else{
                      $sql = "SELECT cod_item FROM itemestoque WHERE cod_estoque = '$codest' AND cod_item = '$cod1' ";
                      $conexao->query($sql);

                      if($conexao->num_rows() <= 0){
                        $sql = "INSERT INTO itemestoque(cod_item, cod_estoque, qtd_desejada, qtd_estoque) VALUES ('$cod1', '$codest', '$qtd_des', '$qtd_est')";
                        $status = $conexao->query($sql);
                      }
                      header("Refresh: 0; url=processa.php?acao=listaritem");
  ?>                  <script>alert("Adicionado com Sucesso");</script>
  <?php
                    }
                  }

                  if($_GET['acao'] === 'listarUsuariosLocal'){
                    $codest = $_SESSION['cod_estoque'];
                    $sql = "SELECT cod_usuario, nome, email, cod_estoque FROM usuario WHERE cod_estoque = '$codest'";
                    $conexao->query($sql);

                    echo "<br><br>";
                    echo "<table class='table table-hover'>";
  ?>
                    <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button>
  <?php
                    $headerFlag = FALSE;

                    for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                      echo "<tr class='table-active'>";
                      foreach ($tupla as $key => $value){
                        if($headerFlag === FALSE){
                          echo "<th>$key </th>";
                        }else{
                          echo "<td>$value </td>";
                        }
                      }
                      echo "</tr>";

                      echo "<tr>";
                      if($headerFlag === FALSE){
                        echo "<br>";
                        foreach ($tupla as $key => $value){
                          echo "<td>$value </td>";
                        }
                        $headerFlag = TRUE;
                      }
                      echo "<br>";
                    }
                    echo "</table>";
                  }

                  if($_GET['acao'] === 'atualizaItem'){//marca
                    $cod1 = $_GET['item'];
                    $codest = $_SESSION['cod_estoque'];
                    $qtd_des = $_POST['qtd_desejada'];
                    $qtd_est = $_POST['qtd_estoque'];

                    if($qtd_des == "" || $qtd_des == "" || $qtd_des < 0 || $qtd_est < 0){
                      header("Refresh: 0; url=processa.php?acao=acessaestoque");
  ?>                  <script>alert("erro, preencha os campos corretamente");</script>
  <?php
                    }else{
                      $sql = "SELECT cod_item FROM itemestoque WHERE cod_estoque = '$codest'";
                      $conexao->query($sql);

                      if($conexao->num_rows() >= 1){
                        $sql = "UPDATE itemestoque SET qtd_desejada = '$qtd_des', qtd_estoque = '$qtd_est' WHERE itemestoque.cod_item = '$cod1' AND itemestoque.cod_estoque = '$codest'";
                        $status = $conexao->query($sql);
                      }

                      header("Refresh: 0; url=processa.php?acao=acessaestoque");
  ?>                  <script>alert("Atualizado com Sucesso");</script>
  <?php
                    }
                  }

                  if($_GET['acao'] === 'listaritem'){
                    $sql = "SELECT * FROM item";
                    $i = 0;
                    $conexao->query($sql);
  ?>                <br><br>
                    <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
                    <button onclick="window.location.href='buscarItem.html'" class="btn btn-block btn-md btn-outline-success">Buscar Itens</button><br>
  <?php
                    echo "<br>";
                    echo "<table class='table table-hover'>";
                    echo "<tr class='table-active'>";
                    echo "<th>ID Item</th>";
                    echo "<th>Descrição</th>";
                    echo "<th>Categoria</th>";
                    echo "<th>Mínimo Desejado</th>";
                    echo "<th>Disponível em Estoque</th>";
                    echo "<th>Adiconar ao Estoque</th>";
                    echo "</tr>";

                    for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                      $i = $i + 1;
                      echo "<tr> <form action='processa.php?acao=adicionaItem&item=".$tupla['cod_item']."' method='POST' name='dados' onSubmit='return adicionaitem();'>";

                      echo "<td>".$tupla['cod_item']."</td> ";
                      echo "<td>".$tupla['descricao']."</td> ";
                      echo "<td>".$tupla['categoria']."</td> ";
  ?>
                          <td><input type="number" name="qtd_desejada" id="qtd_desejada" class="btn btn-block btn-md btn-outline-warning"></td>
                          <td><input type="number" name="qtd_estoque" id="qtd_estoque" class="btn btn-block btn-md btn-outline-primary"></td>
                          <td><input type="submit" name="Adicionar" class="btn btn-block btn-md btn-outline-success"></td>
                          <?php
                          echo "</form></tr>";

                    }
                    echo "</table>";
                  }

                  if($_GET['acao'] === 'compraItem'){
                    $cod1 = $_GET['item'];
                    $codest = $_SESSION['cod_estoque'];
                    $qtd_compra = $_POST['qtd_comprar'];
                    $qtd_est = $_POST['qtd_estoque'];

                    if($qtd_compra == "" || $qtd_est == "" || $qtd_est < 0 || $qtd_compra < 0){
                      header("Refresh: 0; url=processa.php?acao=novalistacompra");
  ?>                  <script>alert("erro, preencha os campos corretamente");</script>
  <?php
                    }else{
                      $qtd_est = $_POST['qtd_estoque'] + $qtd_compra;
                      $sql = "SELECT cod_item FROM itemestoque WHERE cod_estoque = '$codest'";
                      $conexao->query($sql);

                      if($conexao->num_rows() >= 1){
                        $sql = "UPDATE itemestoque SET qtd_estoque = '$qtd_est' WHERE itemestoque.cod_item = '$cod1' AND itemestoque.cod_estoque = '$codest'";
                        $status = $conexao->query($sql);
                      }
                      header("Refresh: 0; url=processa.php?acao=novalistacompra");
  ?>                  <script>alert("Comprado com Sucesso");</script>
  <?php
                    }
                  }

                  if($_GET['acao'] === 'novalistacompra'){
                    $codest1 = $_SESSION['cod_estoque'];
                    $i = 0;
                    $sql = "SELECT itemestoque.cod_item, item.descricao, item.categoria, itemestoque.qtd_desejada, itemestoque.qtd_estoque, itemestoque.cod_estoque
                    FROM itemestoque INNER JOIN item ON item.cod_item = itemestoque.cod_item WHERE itemestoque.cod_estoque = '$codest1'";

                    $conexao->query($sql);
                    $numeroDeItens = $conexao->num_rows();
  ?>                <br><br>
                    <button type="button" onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
  <?php
                    echo "<br>";
                    echo "<table class='table table-hover'>";
                    echo "<tr class='table-active'>";
                    echo "<th>ID Item</th>";
                    echo "<th>Item</th>";
                    echo "<th>Categoria</th>";
                    echo "<th>Mínimo Desejado</th>";
                    echo "<th>Disponível em Estoque</th>";
                    echo "<th>Quantidade a Comprar</th>";
                    echo "<th>Enviar</th>";
                    echo "</tr>";

                    for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                      $i = $i + 1;

                      if($tupla['qtd_desejada'] > $tupla['qtd_estoque']){
                        echo "<tr> <form action='processa.php?acao=compraItem&item=".$tupla['cod_item']."' method='POST' name='dados'>";
                        echo "<td>".$tupla['cod_item']."</td> ";
                        echo "<td>".$tupla['descricao']."</td> ";
                        echo "<td>".$tupla['categoria']."</td> ";
                        echo "<td>".$tupla['qtd_desejada']."</td> ";
                        echo "<td><input type='number' value=".$tupla['qtd_estoque']." id='qtd_estoque' name='qtd_estoque' class='btn btn-block btn-md btn-outline-warning' readonly ></td> ";
                        $qtd_comprar = $tupla['qtd_desejada'] - $tupla['qtd_estoque'];
                        echo "<td><input type='number' value=".$qtd_comprar." id='qtd_comprar' name='qtd_comprar' class='btn btn-block btn-md btn-outline-primary'></td> ";
  ?>                    <td><input type="submit" name="Comprar" class="btn btn-block btn-md btn-outline-success"></td>
  <?php
                        echo "</form></tr>";
                      }
                    }//novo item local

                    echo "</table>";
                  }

                  if($_GET['acao'] === 'acessaestoque'){//atualiza todos
                    $codest1 = $_SESSION['cod_estoque'];
                    $i = 0;
                    $sql = "SELECT itemestoque.cod_item, item.descricao, item.categoria, itemestoque.qtd_desejada, itemestoque.qtd_estoque, itemestoque.cod_estoque FROM itemestoque INNER JOIN item ON item.cod_item = itemestoque.cod_item WHERE itemestoque.cod_estoque = '$codest1'";
                    $conexao->query($sql);
                    $numeroDeItens = $conexao->num_rows();
  ?>                <br><br>
                    <button type="button" onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
  <?php
                    echo "<br>";
                    echo "<form action='processa.php?acao=atualizaTodos' method='POST' name='todos'>";//atualiza todos
                    echo "$numeroDeItens Item(s) encontrado(s).<br>";
                    echo "<table class='table table-hover'>";
                    echo "<tr class='table-active'>";
                    echo "<th>ID Item</th>";
                    echo "<th>Descrição</th>";
                    echo "<th>Categoria</th>";
                    echo "<th>Mínimo Desejado</th>";
                    echo "<th>Disponível em Estoque</th>";
                    echo "<th>ID Estoque</th>";
                    echo "<th>Atualizar</th>";
                    echo "</tr>";

                    for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                      $i = $i + 1;

                      echo "<tr> <form action='processa.php?acao=atualizaItem&item=".$tupla['cod_item']."' method='POST' name='dados'>";
                      echo "<td>".$tupla['cod_item']."</td> ";
                      echo "<td>".$tupla['descricao']."</td> ";
                      echo "<td>".$tupla['categoria']."</td> ";
                      echo "<td><input type='number' value=".$tupla['qtd_desejada']." id='$i' name='qtd_desejada' class='btn btn-block btn-md btn-outline-warning'></td> ";
                      $i = $i + 1;
                      echo "<td><input type='number' value=".$tupla['qtd_estoque']." id='$i' name='qtd_estoque' class='btn btn-block btn-md btn-outline-primary'></td> ";
                      echo "<td>".$tupla['cod_estoque']."</td> ";
  ?>                  <td><input type="submit" name="Atualizar" class="btn btn-block btn-md btn-outline-success"></td>
  <?php
                      echo "</form></tr>";
                    }
                    echo "</table>";

                    //<br><button type="button" onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-primary">Adicionar Todos</button><br> fazer
                    echo "</form>";
                  }
                }
              }
            }

            if($_SERVER['HTTP_REFERER'] === $url.'buscarItem.html'){
              $cod_item = $_POST['cod_item'];
              $descricao = $_POST['descricao'];
              $categoria = $_POST['categoria'];
              $i = 0;
              $sql = "SELECT u.cod_item AS cod_item , u.descricao AS descricao, u.categoria AS categoria FROM item u ";
              $where = "";
              $and = "";

              if(empty($cod_item) === FALSE){
                $where = "WHERE u.cod_item LIKE '$cod_item'";
                $and = " AND ";
              }

              if(empty($descricao) === FALSE){
                if($and == TRUE){
                  $where = $where.$and."descricao LIKE '%$descricao%'";
                }else{
                  $where = "WHERE descricao LIKE '%$descricao%'";
                  $and = " AND ";
                }
              }

              if(empty($categoria) === FALSE){
                if($and == TRUE){
                  $where = $where.$and."categoria LIKE '%$categoria%'";
                }else{
                  $where = "WHERE categoria LIKE '%$categoria%'";
                }
              }

              $sql = $sql.$where." ORDER BY u.cod_item DESC";

              $conexao->query($sql);
              $numeroDeUsuarios = $conexao->num_rows();

  ?>          <br><br>
              <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
              <button onclick="window.location.href='processa.php?acao=listaritem'" class="btn btn-block btn-md btn-outline-success">Todos os Itens</button><br>
              <button onclick="window.location.href='buscarItem.html'" class="btn btn-block btn-md btn-outline-success">Buscar Novamente</button><br>
  <?php
              echo "<br>";
              echo "$numeroDeUsuarios Item(s) encontrado(s).<br>";
              echo "<table class='table table-hover'>";
              echo "<tr class='table-active'>";
              echo "<th>ID Item</th>";
              echo "<th>Descrição</th>";
              echo "<th>Categoria</th>";
              echo "<th>Mínimo Desejado</th>";
              echo "<th>Disponível em Estoque</th>";
              echo "<th>Adicionar ao Estoque</th>";
              echo "</tr>";

              for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                $i = $i + 1;

                echo "<tr> <form action='processa.php?acao=adicionaItem&item=".$tupla['cod_item']."' method='POST' name='dados' onSubmit='return adicionaitem();'>";
                echo "<td>".$tupla['cod_item']."</td> ";
                echo "<td>".$tupla['descricao']."</td> ";
                echo "<td>".$tupla['categoria']."</td> ";
  ?>            <td><input type="number" name="qtd_desejada" id="qtd_desejada" class="btn btn-block btn-md btn-outline-warning"></td>
                <td><input type="number" name="qtd_estoque" id="qtd_estoque" class="btn btn-block btn-md btn-outline-primary"></td>
                <td><input type="submit" name="Adicionar" class="btn btn-block btn-md btn-outline-success"></td>

                <script>
                  function adicionaitem(){
                      var qtd_desejada, qtd_estoque;

                      if(document.dados.qtd_desejada.value == "" || document.dados.qtd_desejada.value <= 0){
                        alert( "Preencha campo MÍNIMO DESEJADO corretamente!" );
                        document.dados.qtd_desejada.focus();
                        return false;
                      }
                      
                      if(document.dados.qtd_estoque.value == "" || document.dados.qtd_estoque.value <= 0){
                        alert( "Preencha campo DISPONÍVEL EM ESTOQUE corretamente!" );
                        document.dados.qtd_estoque.focus();
                        return false;
                      }
                  }
                </script>
  <?php
                echo "</form></tr>";
              }
              echo "</table>";
            
            }else{

              if($_SERVER['HTTP_REFERER'] === $url.'buscarUsuario.html'){
                $conteudo = $_POST['palavra-chave'];
                $categoria = $_POST['categoria'];

                if($categoria === 'nome'){
                  $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u WHERE $categoria LIKE '%$conteudo%'";
                }else{

                  if($categoria === 'login'){
                    $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u WHERE $categoria LIKE '%$conteudo%'";
                  }else{

                    if($categoria === 'permissao'){
                      $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u WHERE $categoria LIKE '%$conteudo%'";
                    }else{

                      if($cod_usuario === 'cod_usuario'){
                        $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u WHERE $categoria LIKE '%$conteudo%'";
                      }else{

                        if($cod_estoque === 'cod_estoque'){
                          $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u WHERE $categoria LIKE '%$conteudo%'";
                        }
                      }
                    }
                  }
                }

                $conexao->query($sql);
                $numeroDeUsuarios = $conexao->num_rows();
  ?>            <br><br>
                <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
  <?php
                echo "<br>";
                echo "$numeroDeUsuarios usuário(s) encontrado(s).<br>";
                echo "<table class='table table-hover'>";
                echo "<tr class='table-active'>";
                echo "<th>Nome</th>";
                echo "<th>Email</th>";
                echo "<th>Permissão</th>";
                echo "<th>ID Usuário</th>";
                echo "<th>ID Estoque</th>";
                echo "</tr>";

                for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                  echo "<tr>";
                  echo "<td>".$tupla['nome']."</td> ";
                  echo "<td>".$tupla['email']."</td> ";
                  echo "<td>".$tupla['permissao']."</td> ";
                  echo "<td>".$tupla['cod_usuario']."</td> ";
                  echo "<td>".$tupla['cod_estoque']."</td> ";
                  echo "</tr>";
                }

                echo "</table>";
              
              }else{
              
                if($_SERVER['HTTP_REFERER'] === $url.'buscarItemAvancado.html'){//mudar
                  $i = 0;

                  $cod_item = $_POST['cod_item'];
                  $descricao = $_POST['descricao'];
                  $categoria = $_POST['categoria'];
                  $sql = "SELECT n.cod_item AS cod_item, n.descricao AS descricao, u.categoria AS categoria FROM item n ";

                  $where = "";
                  $and = "";

                  if(empty($cod_item) === FALSE){
                    $where = "WHERE u.cod_item like '%$cod_item%'";
                    $and = " AND ";
                  }

                  if(empty($descricao) === FALSE){
                    if($and == TRUE){
                      $where = $where.$and."descricao LIKE '%$descricao%'";
                    }else{
                      $where = "WHERE descricao LIKE '%$descricao%'";
                      $and = " AND ";
                    }
                  }

                  if(empty($categoria) === FALSE){
                    if($and == TRUE){
                      $where = $where.$and."categoria like '%$categoria%'";
                    }else{
                      $where = "WHERE categoria like '%$categoria%'";
                    }
                  }

                  $sql = $sql.$where." ORDER BY u.cod_item DESC";
                  $conexao->query($sql);
                  $numeroDeNoticias = $conexao->num_rows();

  ?>              <br><br>
                  <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
                  <button onclick="window.location.href='processa.php?acao=listaritem'" class="btn btn-block btn-md btn-outline-success">Todos os Itens</button><br>
                  <button onclick="window.location.href='buscarItem.html'" class="btn btn-block btn-md btn-outline-success">Buscar Novamente</button>
  <?php
                  echo "<br>";
                  echo "$numeroDeUsuarios Item(s) encontrado(s).<br>";
                  echo "<table class='table table-hover'>";
                  echo "<tr class='table-active'>";
                  echo "<th>ID Item</th>";
                  echo "<th>Descrição</th>";
                  echo "<th>Categoria</th>";
                  echo "<th>Mínimo Desejado</th>";
                  echo "<th>Disponível em Estoque</th>";
                  echo "<th>Adicionar ao Estoque</th>";
                  echo "</tr>";

                  for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                    $i = $i + 1;

                    echo "<tr> <form action='processa.php?acao=adicionaItem&item=".$tupla['cod_item']."' method='POST' name='dados' onSubmit='return adicionaitem();'>";
                    echo "<td>".$tupla['cod_item']."</td> ";
                    echo "<td>".$tupla['descricao']."</td> ";
                    echo "<td>".$tupla['categoria']."</td> ";
  ?>
                    <td><input type="number" name="qtd_desejada" id="qtd_desejada" class="btn btn-block btn-md btn-outline-warning"></td>
                    <td><input type="number" name="qtd_estoque" id="qtd_estoque" class="btn btn-block btn-md btn-outline-primary"></td>
                    <td><input type="submit" name="Adicionar" class="btn btn-block btn-md btn-outline-success"></td>

                    <script>
                      function adicionaitem(){
                          var qtd_desejada, qtd_estoque;

                          if(document.dados.qtd_desejada.value == "" || document.dados.qtd_desejada.value <= 0){
                            alert( "Preencha campo MÍNIMO DESEJADO corretamente!" );
                            document.dados.qtd_desejada.focus();
                            return false;
                          }

                          if(document.dados.qtd_estoque.value == "" || document.dados.qtd_estoque.value <= 0){
                            alert( "Preencha campo DISPONÍVEL EM ESTOQUE corretamente!" );
                            document.dados.qtd_estoque.focus();
                            return false;
                          }
                      }
                    </script>
  <?php
                    echo "</form></tr>";
                  }
                echo "</table>";
                }

                if($_SERVER['HTTP_REFERER'] === $url.'cadastroUsuario_comEstoque.html'){
                  $email = $_POST['email'];
                  $senha = $_POST['senha'];
                  $confirmarSenha = $_POST['confirmarSenha'];
                  $nome = $_POST['nome'];
                  $cod_estoque = $_POST['cod_estoque'];

                  if((empty($senha) == TRUE) || (empty($nome) == TRUE) || (empty($email) == TRUE) || (empty($confirmarSenha) == TRUE) || (empty($cod_estoque) == TRUE)){
                    header("Refresh: 0; url=cadastroUsuario_comEstoque.html");
  ?>                <script>alert("Você deve preencher todos os campos corretamente!");</script>
  <?php
                    exit(0);
                  }

                  if($senha !== $confirmarSenha){
                    header("Refresh: 0; url=cadastroUsuario_comEstoque.html");
  ?>                <script>alert("Senhas não correspondem.");</script>
  <?php
                    exit(0);
                  }

                  $senha = sha1($senha);
                  $sql = "INSERT INTO usuario(nome, email, senha, permissao, cod_estoque) VALUES ('$nome', '$email', '$senha', 'usuario', '$cod_estoque')";
                  $status = $conexao->query($sql);

                  if($status === TRUE){
                    header("Refresh: 0; url=menu.php");
  ?>                <script>alert("Cadastro feito com sucesso");</script>
  <?php
                    exit(0);

                  }
                }

                if($_SERVER['HTTP_REFERER'] === $url.'cadastroUsuario_semEstoque.html'){
                  $email = $_POST['email'];
                  $senha = $_POST['senha'];
                  $confirmarSenha = $_POST['confirmarSenha'];
                  $nome = $_POST['nome'];
                  $descricao = $_POST['descricao'];//descricao do estoque
                  $cod_estoque = 0;

                  if((empty($senha) == TRUE) || (empty($nome) == TRUE) || (empty($email) == TRUE) || (empty($confirmarSenha) == TRUE) || (empty($descricao) == TRUE)){
                    header("Refresh: 0; url=cadastroUsuario_semEstoque.html");
  ?>                <script>alert("Você deve preencher todos os campos corretamente!");</script>
  <?php
                    exit(0);
                  }

                  if($senha !== $confirmarSenha){
                    header("Refresh: 0; url=cadastroUsuario_semEstoque.html");
  ?>                <script>alert("Senhas não correspondem");</script>
  <?php
                    exit(0);
                  }

                  $senha = sha1($senha);
                  $sql = "INSERT INTO estoque(cod_estoque, descricao)	VALUES (NULL, '$descricao')";
                  $status = $conexao->query($sql);

                  if($status === TRUE){
                    echo "Nova Dispensa Cadastrada!";
                  }

                  $sql = "SELECT cod_estoque FROM estoque WHERE descricao = '$descricao'";
                  $status = $conexao->query($sql);

                  if($conexao->num_rows() > 0){
                    $tupla = $conexao->fetch_assoc();
                    $cod_estoque = $tupla['cod_estoque'];
                  }

                  $sql = "INSERT INTO usuario(nome, email, senha, permissao, cod_estoque) VALUES
                  ('$nome', '$email', '$senha', 'usuario', '$cod_estoque')";
                  $status = $conexao->query($sql);

                  if($status === TRUE){
                    header("Refresh: 0; url=menu.php");
  ?>                <script>alert("Cadastro feito com sucesso!");</script>
  <?php
                    exit(0);
                  }
                }else{

                  if($_SERVER['HTTP_REFERER'] === $url.'buscarUsuarioAvancado.html'){
                    $nome = $_POST['nome'];
                    $email = $_POST['email'];
                    $permissao = $_POST['permissao'];
                    $cod_usuario = $_POST['cod_usuario'];
                    $cod_estoque = $_POST['cod_estoque'];
                    $sql = "SELECT u.nome AS nome, u.email AS email, u.permissao AS permissao, u.cod_usuario AS cod_usuario, u.cod_estoque AS cod_estoque FROM usuario u ";
                    $where = "";
                    $and = "";

                    if(empty($nome) === FALSE){
                      $where = "WHERE u.nome like '%$nome%'";
                      $and = " AND ";
                    }

                    if(empty($email) === FALSE){
                      if($and == TRUE){
                        $where = $where.$and."email LIKE '%$email%'";
                      }else{
                        $where = "WHERE email LIKE '%$email%'";
                        $and = " AND ";
                      }
                    }

                    if(empty($permissao) === FALSE){
                      if($and == TRUE){
                        $where = $where.$and."permissao like '%$permissao%'";
                      }else{
                        $where = "WHERE permissao like '%$permissao%'";
                      }
                    }

                    if(empty($cod_usuario) === FALSE){
                      if($and == TRUE){
                        $where = $where.$and."cod_usuario like '%$cod_usuario%'";
                      }else{
                        $where = "WHERE cod_usuario like '%$cod_usuario%'";
                      }
                    }

                    if(empty($cod_estoque) === FALSE){
                      if($and == TRUE){
                        $where = $where.$and."cod_estoque like '%$cod_estoque%'";
                      }else{
                        $where = "WHERE cod_estoque like '%$cod_estoque%'";
                      }
                    }

                    $sql = $sql.$where." ORDER BY u.cod_usuario DESC";
                    $conexao->query($sql);
                    $numeroDeUsuarios = $conexao->num_rows();

  ?>                <button onclick="window.location.href='menu.php'" class="btn btn-block btn-md btn-outline-success">Voltar ao Menu</button><br>
  <?php
                    echo "<br>";
                    echo "$numeroDeUsuarios usuário(s) encontrado(s).<br>";
                    echo "<table class='table table-hover'>";
                    echo "<tr class='table-active'>";
                    echo "<th>Nome</th>";
                    echo "<th>Email</th>";
                    echo "<th>Permissão</th>";
                    echo "<th>ID Usuário</th>";
                    echo "<th>ID Estoque</th>";
                    echo "</tr>";

                    for($tupla = $conexao->fetch_assoc(); $tupla != NULL; $tupla = $conexao->fetch_assoc()){
                      echo "<tr>";
                      echo "<td>".$tupla['nome']."</td> ";
                      echo "<td>".$tupla['email']."</td> ";
                      echo "<td>".$tupla['permissao']."</td> ";
                      echo "<td>".$tupla['cod_usuario']."</td> ";
                      echo "<td>".$tupla['cod_estoque']."</td> ";
                      echo "</tr>";
                    }

                    echo "</table>";
                  }
                }
              }
            }
          }
        }
      }
    }
  ?>
        </div>
        <div class="col-md-3">
        </div>
      </div>
    </div>
  </body>
</html>
