# Proposal

## Why

O app só tem o tema claro, embora o design kit QUALITY ASSURANCE CONSULTANT já defina os tokens do tema escuro (fundo `#111111`, superfícies `#2B2B2B`, controles em amarelo de marca) e as versões escuras do logo. Quem usa o sistema em modo escuro, ou apresenta em sala com projetor escurecido, recebe uma tela branca que não acompanha a preferência do sistema.

## What Changes

- Definir os dois temas nativos do Streamlit (`[theme.light]` e `[theme.dark]` em `.streamlit/config.toml`) com os tokens do kit. O app passa a seguir o tema do sistema operacional, e o usuário pode escolher Claro, Escuro ou Sistema no menu nativo ⋮ do canto superior direito (itens System, Light e Dark), sem recarregar a página e sem perder o resultado na tela.
- Tornar o CSS próprio do app (cabeçalho, cards, métricas, badges, botões, estado vazio, barra lateral) sensível ao tema ativo, usando os tokens escuros do kit quando o tema for escuro.
- Usar as versões escuras do logo horizontal e do símbolo do pato no tema escuro (chapéu claro), como o kit exige para fundos escuros.
- Diagrama Mermaid e cores de status (APROVADO/FALHOU) nas variantes escuras dos tokens (`status-success #4ADE80`, `status-error #F97066`), para manter o contraste.
- Uma legenda curta na barra lateral indicando onde trocar o tema.

Fora de escopo: um botão próprio de troca de tema dentro do app. O Streamlit 1.65 não tem API para trocar o tema pelo código; o único caminho seria gravar uma chave interna não documentada e recarregar a página, o que apagaria o resultado da sessão. A troca fica no menu nativo.

## Capabilities

### New Capabilities
<!-- Nenhuma: o tema escuro faz parte da identidade visual já especificada. -->

### Modified Capabilities
- `identidade-visual`: passa a exigir os dois temas do kit (seleção pelo menu nativo e acompanhamento do sistema). Os requisitos de paleta, logo, hierarquia de ações, status de teste e diagrama deixam de citar só os valores do tema claro e passam a valer para os dois temas. Entra uma indicação de onde trocar o tema.

## Impact

- `.streamlit/config.toml`: seções `[theme.light]` e `[theme.dark]` (com `[theme.dark.sidebar]` se necessário), incluindo as cores de alerta por tema.
- `app.py`: tokens escuros, CSS com variáveis por tema, detecção do tema ativo, logo e símbolo por tema, Mermaid e `tabela_cenarios` com cores por tema, legenda na barra lateral.
- `tests/test_interface.py`: testes para tokens escuros contra o kit, config dos dois temas e CSS por tema.
- `README.md`: como alternar o tema.
- Sem novas dependências.
