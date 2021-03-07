<?php
	class Connection
	{
		var $host;
		var $user;
		var $password;
		var $database;
		var $link = 0;
		var $result = FALSE;

		function __construct($host, $user, $password, $database)
		{
			$this->host = $host;
			$this->user = $user;
			$this->password = $password;
			$this->database = $database;

			$this->link = mysqli_connect($host, $user, $password, $database);
			$this->setCharSet("utf8");
		}

		function close()
		{
			mysqli_close($this->getLink());
		}

		function getLink()
		{
			return $this->link;
		}

		function getResult()
		{
			return $this->result;
		}

		function errorMessage()
		{
			echo "Um erro ocorreu!<br>";
			echo mysqli_error($this->getLink());
			echo "<br>Código do erro: ";
			echo mysqli_errno($this->getLink());
			echo "<br>";
		}

		function fetch_assoc()
		{
			return mysqli_fetch_assoc($this->getResult());
		}

		function fetch_row()
		{
			return mysqli_fetch_row($this->getResult());
		}

		function num_rows()
		{
			return mysqli_num_rows($this->getResult());
		}

		function query($sql)
		{
			$this->result = mysqli_query($this->getLink(), $sql);

			if($this->getResult() == FALSE)
			{
				echo $this->errorMessage();
				return FALSE;
			}
			else
			{
				return TRUE;
			}
		}

		function setCharSet($charset)
		{
			mysqli_set_charset($this->getLink(), $charset);
		}
	}
?>