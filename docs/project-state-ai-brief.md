# Aegis - resume d'etat du projet et du modele de donnees

Date de l'analyse: 2026-04-17

## But du document

Ce document sert de brief d'onboarding pour un humain ou une IA qui reprend le projet Aegis.

Il explique:

- ce qui est deja implemente
- quelles sont les vraies sources de verite
- comment le repo est structure aujourd'hui
- comment la base est modelee
- quels choix de modelisation semblent deja actes
- quelles zones restent transitoires ou incompletes

L'idee est d'aider une IA a continuer l'architecture existante, sans reintroduire des choix qui iraient contre la direction deja prise.

## TL;DR pour une IA

- La vraie source de verite DB est `supabase/migrations/`.
- `supabase/drafts/` contient des brouillons, pas le canon.
- L'architecture runtime vise `Frontend -> FastAPI backend -> Postgres dans Supabase local`.
- Le navigateur n'est pas cense interroger directement les tables metier.
- La frontiere de tenant est `id_org`.
- Les references partagees sont globales, surtout `currencies` et `asset_classes`.
- La plupart des tables metier utilisent une PK numerique et un `uuid` secondaire.
- Le modele trade est `trades` (header) + `trade_disc` (detail DISC) + `trade_disc_legs` + tables optionnelles 1:1 par leg.
- Le modele reporting est oriente snapshots: une table header + une table rows par dataset.
- Les datasets intraday sont regroupes par `ingestion_runs`.
- `SIMM` reste journalier et independant de `ingestion_runs`.
- `AUM` est aussi journalier et modele a part; il a un `id_run`, mais il n'est pas relie aujourd'hui a `ingestion_runs`.
- La securite actuelle est backend-oriented: `anon` et `authenticated` sont revoques sur `public`, mais il n'y a pas encore de RLS.
- Les APIs backend actuelles sont le vrai contrat operationnel. Il ne faut pas remettre du direct frontend -> Supabase pour la donnee metier.
- `risk` est seulement partiellement reel: la route existe, mais ses tables ne sont pas dans l'historique de migrations.
- `recap` est cable uniquement cote frontend; il n'y a pas encore d'API backend recap.

## Ce qu'il faut croire, dans cet ordre

Si une IA rencontre des informations contradictoires, il faut faire confiance au repo dans cet ordre:

1. `supabase/migrations/`
2. `src/backend/app/infrastructure/persistence/postgres/`
3. `src/backend/app/domain/`
4. `supabase/tests/`
5. `supabase/seed.sql`
6. `supabase/drafts/`
7. `docs/database-supabase-backend-report.md`

Note importante:

- `docs/database-supabase-backend-report.md` reste utile comme contexte historique, mais ce n'est plus la meilleure source pour l'etat courant.

## Structure du repository

```text
docs/
  database-supabase-backend-report.md   Analyse historique
  project-state-ai-brief.md             Ce document

src/
  backend/                              App FastAPI, services domaine, adapters persistence
  frontend/                             App React/Vite qui appelle le backend

supabase/
  config.toml                           Config locale Supabase CLI
  migrations/                           Historique canonique du schema
  seed.sql                              Seed locale de references partagees
  tests/                                Tests pgTAP de regression
  drafts/                               SQL non canonique
  functions/                            Placeholder pour edge functions
```

## Architecture runtime

Flux cible actuel:

```text
Frontend -> FastAPI backend -> Postgres (dans la stack Supabase locale)
```

Concretement:

- le frontend passe par `src/frontend/src/lib/backendClient.ts`
- le frontend cible `VITE_BACKEND_API_URL`, par defaut `http://localhost:8000/api/v1`
- le backend choisit son mode de persistence via `AEGIS_PERSISTENCE_BACKEND`
- dans le vrai chemin, le backend utilise un acces Postgres direct via `AEGIS_DATABASE_URL`
- la stack Supabase locale fournit Postgres, le gateway local, Studio, auth et les services annexes

Le projet est donc deja beaucoup plus proche d'une architecture 3-tier que d'une app navigateur -> Supabase.

## Etat d'implementation actuel

### Flows reellement implementes de bout en bout

- lecture des references partagees: asset classes, currencies
- lecture des references scopees tenant: funds, books, counterparties, trade labels
- lecture des trade types
- listing des trades
- creation d'un trade DISC
- lecture d'un aggregate DISC
- listing du catalogue de datasets snapshots
- listing des snapshots par dataset
- lecture d'un snapshot par dataset et id
- creation d'un snapshot pour les datasets enregistres
- health backend et login quote

### Flows existants mais transitoires

- `risk` a une route API et une consommation frontend, mais la route s'appuie sur des tables absentes des migrations Supabase actuelles
- `TradeChecker` reste un placeholder frontend
- `TradeRecap` est cable en frontend, mais les routes backend recap n'existent pas
- le frontend derive encore `id_org` de `VITE_DEFAULT_ORG_ID`; il n'y a pas de vrai switch tenant ni de resolution tenant basee sur l'auth

### Couverture du seed

`supabase/seed.sql` seed seulement:

- `currencies`
- `asset_classes`

Il ne seed pas encore les rows metier scopees tenant comme:

- organisations
- users
- funds
- books
- counterparties
- trade labels

Donc le backend peut demarrer, mais beaucoup d'endpoints scopes tenant renverront des listes vides tant que les donnees n'ont pas ete inserees.

## Vue d'ensemble de la base

La base est aujourd'hui un design mono-schema `public`, mais avec une posture d'acces orientee backend.

Il y a 47 tables dans l'historique de migrations committe.

On peut les regrouper en 5 familles:

1. references partagees
2. fondation tenant / authz
3. coeur trading
4. snapshots reporting
5. hardening securite / coherence

## Choix de modelisation transverses

Ces choix paraissent intentionnels et devraient etre preserves tant qu'une decision explicite ne les remplace pas.

### 1. Les ids numeriques sont les cles operationnelles

Presque toutes les tables utilisent:

- une PK `BIGSERIAL` pour les joins et le travail applicatif
- un `uuid` secondaire avec contrainte d'unicite

Le backend actuel utilise les ids numeriques, pas les UUIDs.

Implication:

- si un futur contrat API doit exposer des ids externes stables, il faudra le decider explicitement; aujourd'hui le contrat applicatif est numerique

### 2. Le scope tenant est explicite

La frontiere de tenant est `organisation`, via `id_org`.

La plupart des tables metier portent `id_org`, et beaucoup de FKs sont composites:

- `(id_org, id_f)`
- `(id_org, id_user)`
- `(id_org, id_book)`
- `(id_org, id_ctpy)`

C'est un choix central. Toute nouvelle table metier scopee tenant devrait suivre ce pattern.

### 3. Les references partagees restent globales

`currencies` et `asset_classes` sont globales et non scopees tenant.

C'est pourquoi les tables metier referencent souvent:

- `currencies(id_ccy)`
- `asset_classes(id_ac)`

sans inclure `id_org`.

### 4. Les statuts et flags "official" sont modeles en base

Le design ne repose pas seulement sur des payloads bruts. Plusieurs etats sont explicites:

- statut du trade dans `trades`
- statut du snapshot dans chaque table header
- flags `is_official` ou equivalent

La base est censee faire respecter ces invariants via contraintes et indexes uniques.

### 5. Les payloads bruts sont conserves, mais comme stockage secondaire

Plusieurs tables contiennent `payload_json` ou `raw_payload_json`.

Le pattern est:

- les champs stables et importants passent en colonnes relationnelles typees
- les attributs encore mouvants restent aussi preserves en JSONB

C'est utile, mais il ne faut pas laisser ces colonnes devenir un fourre-tout permanent.

### 6. Le backend est la vraie Data API

La direction actuelle est explicite:

- le frontend appelle le backend
- le backend porte les regles metier
- Postgres/Supabase est derriere le backend

Il ne faut pas traiter PostgREST ou le client Supabase navigateur comme l'interface metier principale.

## Famille 1: references partagees

Migration canonique:

- `supabase/migrations/20260409020000_init_shared_reference.sql`

Tables:

- `currencies`
- `asset_classes`

Notes:

- elles sont globales et replay-safe
- ce sont les seules tables seedees par defaut
- elles portent deja `is_active`, `sort_order` et `updated_at`
- `20260414000100_harden_schema_coherence.sql` ajoute des triggers `updated_at` sur les deux

Interpretation:

- ces tables servent a alimenter dropdowns, classification et reporting sur tous les tenants

## Famille 2: fondation tenant et authz

Migration canonique:

- `supabase/migrations/20260409020100_init_authz_reference.sql`

Tables:

- `organisations`
- `offices`
- `departments`
- `office_departments`
- `users`
- `user_offices`
- `user_departments`
- `ranks`
- `user_ranks`
- `access_roles`
- `user_access_roles`

Choix de modelisation importants:

- `organisation` est la racine de tenant
- les utilisateurs sont modeles dans une table applicative `users`
- `users` stocke `entra_oid`, ce qui suggere fortement que Microsoft Entra est l'ancre d'identite visee
- les notes de migration disent explicitement que l'authentification a lieu hors de la base
- les tables de jointure repetent `id_org` pour empecher des liens cross-tenant
- `fund_office_access` prolonge ensuite ce pattern pour les acces fond / office

Hardening ajoute ensuite:

- un seul office primaire actif par user
- un seul office_department primaire actif par office
- un seul rank primaire actif par user
- unicite case-insensitive de l'email au sein d'une organisation
- triggers `updated_at` sur les tables authz/reference principales

Gap important:

- il n'y a aujourd'hui aucun lien entre cette table `users` et `auth.users`
- le backend ne resout pas encore le caller depuis un JWT
- donc le modele de donnees anticipe une couche user/access, mais la couche runtime d'autorisation n'est pas terminee

## Famille 3: coeur trading

Migration canonique:

- `supabase/migrations/20260409020200_init_trade_core.sql`

Tables:

- `funds`
- `fund_office_access`
- `banks`
- `counterparties`
- `books`
- `trade_types`
- `trade_disc_labels`
- `trade_spe`
- `trades`
- `trade_disc`
- `trade_disc_legs`
- `trade_disc_premiums`
- `trade_disc_fields`
- `trade_disc_instruments`
- `trade_disc_settlements`

### Modele trade

Le modele trade est stratifie:

1. `trades`
   Header maitre du trade.

2. `trade_disc`
   Detail specifique au type DISC.

3. `trade_disc_legs`
   Un trade DISC peut avoir plusieurs legs.

4. Tables enfants optionnelles par leg
   `trade_disc_instruments`, `trade_disc_premiums`, `trade_disc_fields`, `trade_disc_settlements`

C'est aujourd'hui le coeur metier le plus concret de l'application.

### Sens des tables principales

- `trade_spe` est l'ancre d'identite du sous-arbre trade
- `trades` stocke les metadonnees de header: organisation, fund, type, user de booking, timestamps, status
- `trade_disc` stocke les metadonnees DISC: book, portfolio, counterparty, label, ids ICE, champs descriptifs
- `trade_disc_legs` stocke une row par leg
- chaque table enfant optionnelle est contrainte a une seule row par leg

### Choix de modelisation importants cote trade

- `id_book` et `id_portfolio` pointent tous les deux vers `books`
- `counterparties` est separe de `banks`, avec lien banque optionnel
- les trade labels sont tenant-scopes via `trade_disc_labels`
- `trade_status` prepare deja un futur workflow:
  `booked`, `recap_done`, `validated`, `rejected`, `cancelled`
- le backend auto-initialise `trade_types` par organisation avec:
  `DISC` et `ADV`

Nuance importante:

- seul `DISC` est implemente de bout en bout aujourd'hui
- `ADV` existe comme type, mais il n'y a pas encore d'aggregate advisory dedie

### Hardening ajoute ensuite

`supabase/migrations/20260414000100_harden_schema_coherence.sql` renforce la coherence trade:

- ajout d'une FK explicite de `trade_disc(id_org, id_spe)` vers `trades(id_org, id_spe)`
- normalisation du `buysell` de `trade_disc_fields` sur `Buy` / `Sell`
- garantie d'un header trade unique par `(id_org, id_spe)`

### Comportement backend lie a ce modele

Le service trade backend n'essaie pas encore d'etre generique.

Il orchestre explicitement:

- creation de `trade_spe`
- creation de `trades`
- creation de `trade_disc`
- creation de chaque leg
- creation eventuelle des rows filles de leg
- rechargement de l'aggregate

Implication:

- toute evolution du modele DISC doit etre repercutee a la fois dans le SQL et dans `src/backend/app/infrastructure/persistence/postgres/trades.py`

## Famille 4: snapshots reporting

Migrations canoniques:

- `supabase/migrations/20260409020300_init_reporting_snapshots.sql`
- `supabase/migrations/20260410000100_add_ingestion_runs.sql`
- `supabase/migrations/20260414000100_harden_schema_coherence.sql`
- `supabase/migrations/20260414000200_add_aum_snapshots.sql`

La zone reporting suit un pattern repete:

- une table header de snapshot
- une table rows
- un code dataset dans le catalogue backend

### Datasets enregistres dans le backend

Le registre des datasets est dans:

- `src/backend/app/domain/data_snapshots/catalog.py`

Datasets actuellement enregistres:

- `AUM`
- `SIMM`
- `EXPIRIES`
- `NAV_ESTIMATED`
- `LEVERAGES`
- `LEVERAGES_PER_TRADE`
- `LEVERAGES_PER_UNDERLYING`
- `LONG_SHORT_DELTA`
- `COUNTERPARTY_CONCENTRATION`

Le mapping SQL qui relie chaque code dataset a ses tables concretes est dans:

- `src/backend/app/infrastructure/persistence/postgres/data_snapshots.py`

Ce mapping fait partie de la vraie source de verite.

### Datasets journaliers

Les datasets journaliers sont aujourd'hui:

- `SIMM`
- `AUM`

#### SIMM

Tables:

- `simm_snapshots`
- `simm_snapshot_rows`

Grain:

- header: un snapshot par fund / jour / load
- rows: une row par counterparty par snapshot

Contraintes importantes:

- plusieurs snapshots non officiels sont permis pour le meme fund et le meme jour
- un seul snapshot officiel est permis par fund et par jour
- l'alignement row/header sur fund et date est force

Sens du design:

- SIMM est traite comme un dataset journalier avec historique de retries et promotion explicite d'un officiel

#### AUM

Tables:

- `aum_snapshots`
- `aum_rows`

Grain:

- un snapshot journalier par fund / load
- une seule row par snapshot

Contraintes importantes:

- un seul snapshot officiel par fund et par jour
- exactement une row par snapshot
- l'alignement row/header sur fund et date est force

Nuance importante:

- `AUM` a un `id_run`, mais il n'y a pas de FK de `aum_snapshots` vers `ingestion_runs`
- aujourd'hui, `AUM` se comporte donc plutot comme un dataset journalier autonome que comme un membre du modele intraday batch

### Datasets intraday regroupes par ingestion_runs

Table batch parent:

- `ingestion_runs`

Familles de snapshots enfants reliees a ce parent:

- `expiries_snapshots`
- `nav_estimated_snapshots`
- `leverages_snapshots`
- `leverages_per_trade_snapshots`
- `leverages_per_underlying_snapshots`
- `long_short_delta_snapshots`
- `counterparty_concentration_snapshots`

Tables rows correspondantes:

- `expiries`
- `nav_estimated`
- `leverages`
- `leverages_per_trade`
- `leverages_per_underlying`
- `long_short_delta`
- `counterparty_concentration`

Sens du design:

- un batch logique intraday peut produire plusieurs familles de datasets
- `ingestion_runs` est l'identifiant parent de ce batch logique
- supprimer le batch parent cascade vers les headers enfants puis vers leurs rows

Cela est verifie par `supabase/tests/002_reporting_snapshot_batches.sql`.

### Pattern de modelisation snapshot

Le pattern est coherent entre datasets:

- le header stocke metadata, champs temporels, source, status, official flag, row_count, notes
- la table rows stocke le grain metier du dataset
- les payloads bruts sont preserves dans `raw_payload_json`
- les rows importantes ont aussi une regle relationnelle d'unicite

Exemples:

- `expiries` est unique par snapshot et `row_hash`
- `leverages_per_trade` est unique par snapshot et `trade_id`
- `long_short_delta` est unique par snapshot et `underlying_asset`
- `counterparty_concentration` est unique par snapshot et `id_ctpy`

### Cas speciaux

`EXPIRIES` est un peu special:

- il utilise `snapshot_date` et `snapshot_ts`
- il utilise historiquement `is_latest_for_day`
- le backend traite `is_latest_for_day = true` ou `status = official` comme "official/latest"

Datasets single-row:

- `AUM`
- `NAV_ESTIMATED`
- `LEVERAGES`

Datasets multi-row:

- `SIMM`
- `EXPIRIES`
- `LEVERAGES_PER_TRADE`
- `LEVERAGES_PER_UNDERLYING`
- `LONG_SHORT_DELTA`
- `COUNTERPARTY_CONCENTRATION`

### Pourquoi c'est important pour la suite

Si un nouveau dataset est ajoute, le pattern deja etabli dans le projet est:

1. ajouter une migration de table header
2. ajouter une migration de table rows
3. ajouter contraintes et indexes du grain du dataset
4. enregistrer le dataset dans `catalog.py`
5. le mapper dans `postgres/data_snapshots.py`
6. l'exposer via les routes backend generiques `/data/{dataset}`
7. ajouter des tests pgTAP sur les invariants critiques

## Famille 5: securite et hardening de coherence

Migration securite:

- `supabase/migrations/20260410001000_lock_down_public_access_until_rls.sql`

Migration coherence:

- `supabase/migrations/20260414000100_harden_schema_coherence.sql`

### Posture de securite actuelle

Ce qui est deja fait:

- `anon` et `authenticated` sont revoques de toutes les tables, sequences et routines de `public`
- les default privileges sont eux aussi revoques pour ces roles
- `service_role` garde tous les acces

Ce qui n'est pas encore fait:

- pas de policies RLS
- pas de policies SQL tenant-aware
- pas de resolution auth -> user cote backend

Interpretation:

- le projet est volontairement dans une phase backend-only
- c'est plus sur qu'un acces navigateur ouvert
- mais ce n'est pas encore un vrai modele complet d'autorisation user-facing

### Hardening de coherence deja en place

La migration de hardening fait deja du vrai travail utile:

- automatisation de `updated_at` sur les tables core/reference/authz
- garantie d'une seule assignation primaire active dans plusieurs tables de jointure
- renforcement de la coherence header/detail cote trade
- renforcement de la coherence row/header cote snapshots
- garantie que les datasets single-row restent single-row

Ce n'est pas cosmetique. Cela fait deja partie du modele cible.

## Ce que le backend suppose actuellement de la base

Le backend fait plusieurs hypothese qui comptent pour la suite.

### Hypotheses reference

- `currencies` et `asset_classes` existent et peuvent etre seedees
- les tables de reference metier sont filtrees par `id_org`
- `trade_disc_labels` est la table canonique pour les labels de trade

### Hypotheses trade

- DISC est la seule famille de trade completement modelisee
- `trade_types` peut etre cree paresseusement pour une organisation
- tous les ids utilises dans les payloads sont des ids numeriques du modele relationnel
- un aggregate trade peut etre recharge par `id_org + id_spe`

### Hypotheses snapshot

- les noms de datasets sont controles par l'enum/catalogue Python
- le backend sait, dataset par dataset, quelle colonne temporelle utiliser
- le backend sait si un dataset est single-row ou multi-row
- le backend recompose les payloads JSON a partir des colonnes normalisees et du JSONB stocke

### Hypotheses securite

- le backend peut se connecter directement a Postgres
- le navigateur n'a pas besoin d'acces direct aux tables

## Tests importants deja presents

`supabase/tests/` verifie deja plusieurs invariants essentiels:

- verrouillage securite du schema `public`
- partage d'un meme batch logique intraday entre plusieurs familles de snapshots
- cascade deletion de `ingestion_runs` vers headers puis rows
- un trade DISC peut porter plusieurs legs
- les tables optionnelles de leg restent 1:1 par leg
- supprimer un leg cascade vers ses sous-tables optionnelles
- un seul snapshot SIMM officiel par fund et par jour
- coherence row/header sur les snapshots
- semantique single-primary pour certaines assignations office/fund

Cela veut dire que le schema n'est plus seulement intentionnel; plusieurs choix structurants sont deja testes.

## Gaps et dette transitoire

Ce sont les points qu'une IA doit traiter comme des zones connues mais non finalisees.

### 1. Le modele risk n'est pas dans le schema canonique

La route backend `src/backend/app/api/v1/routes/risk.py` interroge:

- `risk_categories`
- `risk_control_definitions`
- `risk_control_levels`

Ces tables n'existent pas dans le jeu de migrations committe.

Interpretation:

- la route risk est un pont temporaire, pas encore un module canonique stabilise

### 2. Recap n'est pas implemente cote serveur

Le frontend appelle:

- `GET /recap/run`
- `POST /recap/book`

Mais le backend ne fournit pas encore ces routes.

### 3. L'auth est modelisee mais pas operationalisee

- la DB a `users`, roles, ranks, assignments d'office et tables d'acces
- le backend continue a utiliser des query params comme `id_org` et des champs payload comme `booked_by`
- il n'y a pas encore de resolution identite / tenant via JWT

### 4. `public` reste le schema de tout

Meme si l'acces est verrouille, les tables metier vivent toujours dans `public`.

C'est viable a ce stade, mais ce n'est pas encore un design final de schemas prives / schemas API.

### 5. Les timestamps et `updated_at` ne sont pas homogenes partout

Le trigger automatique `updated_at` n'existe que sur certaines tables core/authz/reference.

Ce n'est pas encore une convention globale sur toutes les tables metier.

## Garde-fous recommandes pour une IA

Si une IA continue ce projet, les regles les plus sures sont:

1. traiter `supabase/migrations/` comme une source de verite append-only
2. ne pas recreer de direct browser -> business tables
3. conserver `id_org` sur toute nouvelle table metier scopee tenant
4. preferer des FKs composites incluant `id_org` pour les relations tenant-scopees
5. pour une nouvelle famille de trade, suivre le pattern aggregate existant plutot que surcharger `trade_disc`
6. pour un nouveau dataset reporting, suivre le pattern header + rows + catalog + mapping + tests
7. continuer a promouvoir en colonnes typees les champs JSON qui deviennent stables
8. ne pas supposer que `risk` est canonique tant que ses migrations n'existent pas
9. ne pas supposer que `recap` existe tant que les routes backend et la persistence ne sont pas la
10. garder le backend comme frontiere de l'autorisation metier, meme si de la RLS arrive plus tard

## Decisions d'architecture qu'il faudra bientot figer

Ces decisions ne sont pas encore completement tranchees, mais ce sont les plus structurantes pour la suite.

### Identite et autorisation

Il faudra decider explicitement si le modele runtime user sera:

- Supabase Auth mappe vers la table `users` existante
- un auth Entra first avec resolution backend
- un modele hybride

Ce qu'il ne faut pas faire:

- utiliser a moitie la table `users` sans modele stable de mapping auth

### Domaine risk

Soit:

- promouvoir risk en vrai schema canonique avec migrations et services domaine

Soit:

- garder risk clairement marque comme placeholder tant que son schema n'est pas pret

### Semantique du `id_run` AUM

Il faut clarifier si `AUM.id_run` doit:

- rester un identifiant de load journalier autonome, comme SIMM

ou:

- finir par s'aligner sur `ingestion_runs`

### Resolution du tenant

Il faudra passer de `id_org` fourni par le frontend a un modele de tenant resolu cote backend une fois l'auth branchee.

## Resume final

Le projet est deja opinionated meme s'il n'est pas termine.

Ce qui est clairement etabli:

- architecture runtime backend-first
- ownership de la base par migrations
- scope tenant par `organisation`
- aggregate DISC comme principal workflow trading
- modele reporting oriente snapshots
- verrouillage explicite des acces navigateur sur `public`

Ce qui manque encore:

- le runtime final d'auth et d'autorisation
- un schema risk canonique
- le backend recap
- des seeds tenant plus riches

Le bon modele mental pour la suite est donc:

- garder le backend comme frontiere metier
- etendre le modele relationnel deliberement
- preserver les invariants tenant-aware dans le SQL
- reutiliser les patterns aggregate et snapshot existants plutot que d'en inventer des paralleles
