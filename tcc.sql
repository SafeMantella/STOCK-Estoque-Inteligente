-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 07-Mar-2021 às 03:24
-- Versão do servidor: 10.4.14-MariaDB
-- versão do PHP: 7.4.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `tcc`
--

-- --------------------------------------------------------

--
-- Estrutura da tabela `estoque`
--

CREATE TABLE `estoque` (
  `cod_estoque` bigint(20) UNSIGNED NOT NULL,
  `descricao` varchar(500) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `item`
--

CREATE TABLE `item` (
  `cod_item` bigint(20) UNSIGNED NOT NULL,
  `descricao` varchar(300) NOT NULL,
  `categoria` varchar(300) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `itemestoque`
--

CREATE TABLE `itemestoque` (
  `cod_item` bigint(20) UNSIGNED NOT NULL,
  `cod_estoque` bigint(20) UNSIGNED NOT NULL,
  `qtd_desejada` int(11) NOT NULL,
  `qtd_estoque` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `listacompra`
--

CREATE TABLE `listacompra` (
  `cod_lista` bigint(20) UNSIGNED NOT NULL,
  `cod_estoque` bigint(20) UNSIGNED NOT NULL,
  `status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `listaitem`
--

CREATE TABLE `listaitem` (
  `cod_item` bigint(20) UNSIGNED NOT NULL,
  `cod_lista` bigint(20) UNSIGNED NOT NULL,
  `qtd_desejada` int(11) NOT NULL,
  `status` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `usuario`
--

CREATE TABLE `usuario` (
  `cod_usuario` bigint(20) UNSIGNED NOT NULL,
  `nome` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `senha` varchar(500) NOT NULL,
  `permissao` varchar(500) NOT NULL,
  `cod_estoque` bigint(20) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Índices para tabelas despejadas
--

--
-- Índices para tabela `estoque`
--
ALTER TABLE `estoque`
  ADD UNIQUE KEY `cod_estoque` (`cod_estoque`);

--
-- Índices para tabela `item`
--
ALTER TABLE `item`
  ADD UNIQUE KEY `cod_item` (`cod_item`);

--
-- Índices para tabela `itemestoque`
--
ALTER TABLE `itemestoque`
  ADD PRIMARY KEY (`cod_item`,`cod_estoque`),
  ADD KEY `cod_estoque` (`cod_estoque`);

--
-- Índices para tabela `listacompra`
--
ALTER TABLE `listacompra`
  ADD UNIQUE KEY `cod_lista` (`cod_lista`),
  ADD KEY `cod_estoque` (`cod_estoque`);

--
-- Índices para tabela `listaitem`
--
ALTER TABLE `listaitem`
  ADD KEY `cod_item` (`cod_item`),
  ADD KEY `cod_lista` (`cod_lista`);

--
-- Índices para tabela `usuario`
--
ALTER TABLE `usuario`
  ADD UNIQUE KEY `cod_usuario` (`cod_usuario`),
  ADD KEY `cod_estoque` (`cod_estoque`);

--
-- AUTO_INCREMENT de tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `estoque`
--
ALTER TABLE `estoque`
  MODIFY `cod_estoque` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `item`
--
ALTER TABLE `item`
  MODIFY `cod_item` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `listacompra`
--
ALTER TABLE `listacompra`
  MODIFY `cod_lista` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `usuario`
--
ALTER TABLE `usuario`
  MODIFY `cod_usuario` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- Restrições para despejos de tabelas
--

--
-- Limitadores para a tabela `itemestoque`
--
ALTER TABLE `itemestoque`
  ADD CONSTRAINT `itemestoque_ibfk_1` FOREIGN KEY (`cod_item`) REFERENCES `item` (`cod_item`),
  ADD CONSTRAINT `itemestoque_ibfk_2` FOREIGN KEY (`cod_estoque`) REFERENCES `estoque` (`cod_estoque`);

--
-- Limitadores para a tabela `listacompra`
--
ALTER TABLE `listacompra`
  ADD CONSTRAINT `listacompra_ibfk_1` FOREIGN KEY (`cod_estoque`) REFERENCES `estoque` (`cod_estoque`);

--
-- Limitadores para a tabela `listaitem`
--
ALTER TABLE `listaitem`
  ADD CONSTRAINT `listaitem_ibfk_1` FOREIGN KEY (`cod_item`) REFERENCES `item` (`cod_item`),
  ADD CONSTRAINT `listaitem_ibfk_2` FOREIGN KEY (`cod_lista`) REFERENCES `listacompra` (`cod_lista`);

--
-- Limitadores para a tabela `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`cod_estoque`) REFERENCES `estoque` (`cod_estoque`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
