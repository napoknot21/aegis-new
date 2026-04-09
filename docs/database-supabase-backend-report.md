# Rapport Database, Supabase et Refonte Backend

Date: 2026-04-09

## 1. Résumé exécutif

Aujourd'hui, ta base Supabase n'est pas encore organisée selon un workflow "source of truth" robuste. Le dossier `src/supabase/` a bien été auto-généré par la CLI, mais sa position et la structure autour des fichiers SQL ne sont pas idéales pour un projet qui veut monter en sécurité.

Les points les plus importants sont:

- le dossier Supabase devrait idéalement vivre à la racine du repo sous `supabase/`, pas sous `src/supabase/`
- `config.toml` peut être versionné, mais ne doit jamais contenir de secrets en dur
- les fichiers `tables.sql`, `insert.sql`, `delete.sql` ne doivent pas devenir la source principale de vérité du schéma
- la vraie source de vérité doit être une suite de migrations versionnées dans `supabase/migrations/`
- les tables métier sensibles ne doivent pas être exposées directement au navigateur
- si tu gardes Supabase, il faut décider très tôt si tu fais une architecture "2-tier" (front -> Supabase) ou "3-tier" (front -> backend -> Postgres/Supabase). Pour Aegis, je recommande clairement une architecture `3-tier`

En l'état, le fichier réellement peuplé n'est pas `src/supabase/db/tables.sql`, mais `src/supabase/db/SCHEMA_VNEXT_CORE_PATCH.sql`. C'est donc ce fichier qu'il faut considérer comme la base fonctionnelle actuelle.

## 2. Ce que j'ai observé dans le dépôt

Structure actuelle pertinente:

```text
src/supabase/
├── .branches/
├── .temp/
├── .gitignore
├── config.toml
└── db/
    ├── SCHEMA_VNEXT_CORE_PATCH.sql
    ├── delete.sql
    ├── insert.sql
    └── tables.sql
```

Constats:

- `config.toml` est bien le fichier standard généré par Supabase CLI
- `.branches/` et `.temp/` sont des artefacts locaux CLI, donc normaux
- `tables.sql`, `insert.sql` et `delete.sql` sont vides
- le SQL métier réel est dans `SCHEMA_VNEXT_CORE_PATCH.sql`
- il n'y a pas de dossier `migrations/`
- il n'y a pas de `seed.sql`
- il n'y a aucune policy RLS visible, aucun `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`, aucun `CREATE POLICY`, aucun `GRANT/REVOKE`

## 3. Comment je te recommande de nommer et organiser le dossier Supabase

### Recommandation principale

Je te recommande de déplacer:

```text
src/supabase
```

vers:

```text
supabase
```

à la racine du dépôt.

### Pourquoi

- c'est le pattern attendu par défaut par la CLI Supabase
- c'est plus lisible pour l'équipe et pour la CI/CD
- ça évite de mélanger le code applicatif (`src/`) avec l'infrastructure de base de données
- ça limite les erreurs de chemins, de scripts et de commandes

### Structure cible recommandée

```text
supabase/
├── config.toml
├── migrations/
│   ├── 202604090001_init_core_schema.sql
│   ├── 202604090002_authz_and_membership.sql
│   ├── 202604090003_rls_policies.sql
│   ├── 202604090004_reference_data.sql
│   └── 202604090005_trade_booking_workflow.sql
├── seed.sql
├── functions/
├── tests/
│   ├── rls.sql
│   ├── memberships.sql
│   └── trade_booking.sql
└── .gitignore
```

### Ce qu'il faut garder

- `supabase/config.toml`
- `supabase/.gitignore`
- `supabase/migrations/`
- `supabase/seed.sql`
- `supabase/tests/`
- éventuellement `supabase/functions/` si tu utilises des Edge Functions

### Ce qu'il ne faut pas utiliser comme source de vérité

- `db/tables.sql`
- `db/insert.sql`
- `db/delete.sql`

Ces fichiers peuvent servir de brouillon temporaire, mais pas de socle principal du projet.

## 4. Règles de nommage recommandées

### Dossier

- `supabase/` pour l'infra Supabase
- `src/backend/` pour le backend applicatif
- `src/frontend/` pour le front

### Migrations

Format recommandé:

```text
YYYYMMDDHHMMSS_description.sql
```

Exemples:

```text
202604090001_init_core_schema.sql
202604090002_create_memberships.sql
202604090003_enable_rls.sql
202604090004_trade_booking_tables.sql
```

### Seeds

Si tu as de la donnée de référence stable:

- `seed.sql` si tu veux un seul fichier
- ou `supabase/seeds/010_reference_data.sql`, `020_demo_data.sql` si tu veux découper

### Scripts SQL hors migrations

Si tu as besoin de scripts ad hoc, garde-les en dehors de la source de vérité, par exemple:

```text
scripts/sql/manual/
scripts/sql/maintenance/
scripts/sql/backfill/
```

Pas dans `supabase/migrations/`, sauf si le changement doit vraiment faire partie de l'historique officiel du schéma.

## 5. Où mettre la configuration et les secrets

### `config.toml`

`supabase/config.toml` est le bon endroit pour:

- les ports locaux
- les options de services locaux
- les chemins de seed
- les schémas exposés localement

Il ne doit pas devenir un coffre à secrets.

### Secrets

Les vraies valeurs sensibles doivent vivre:

- dans des variables d'environnement locales non versionnées
- dans les secrets Supabase côté plateforme
- ou dans un secret manager de CI/CD

### Convention pratique

Versionner:

```text
.env.example
src/backend/.env.example
src/frontend/.env.example
```

Ignorer:

```text
.env
.env.local
.env.*.local
src/backend/.env
src/backend/.env.local
src/frontend/.env
src/frontend/.env.local
supabase/.env
supabase/.env.local
```

### Règles importantes

- `SUPABASE_SERVICE_ROLE_KEY` ne doit jamais apparaître dans le frontend
- `VITE_SUPABASE_ANON_KEY` peut être dans le frontend, mais seulement si RLS est correctement faite
- la connexion Postgres directe et les secrets service role doivent rester côté backend uniquement

## 6. Vecteurs d'attaque principaux sur une stack Supabase

### 6.1 Exposition directe des tables métier

Vecteur:

- le frontend appelle directement des tables sensibles via `anon`
- sans RLS solide, un utilisateur lit ou modifie des données qui ne lui appartiennent pas

Impact:

- fuite de données
- corruption de données
- IDOR horizontal entre fonds/organisations

Mitigation:

- ne pas exposer les tables métier critiques directement au navigateur
- activer RLS explicitement sur toutes les tables exposées
- idéalement placer les tables privées dans un schéma non exposé

### 6.2 Fuite ou mauvais usage de la `service_role`

Vecteur:

- clé copiée dans le frontend
- clé dans le repo
- clé utilisée pour des opérations ordinaires au lieu d'opérations admin strictement serveur

Impact:

- contournement complet de RLS
- exfiltration totale de la base

Mitigation:

- `service_role` uniquement côté backend
- rotation des secrets
- séparation stricte entre use case "user request" et use case "admin/system"

### 6.3 RLS absente ou cassée

Vecteur:

- tables créées en SQL sans `ENABLE ROW LEVEL SECURITY`
- policy trop permissive
- policy qui ne tient pas compte du tenant/fund/org

Impact:

- accès cross-tenant
- écriture non autorisée

Mitigation:

- RLS sur toute table exposée
- tests pgTAP dédiés aux policies
- revue systématique des policies avant mise en production

### 6.4 Schéma public trop exposé

Vecteur:

- tout est mis dans `public`
- PostgREST expose implicitement trop d'objets

Impact:

- surface d'attaque inutilement large

Mitigation:

- garder un schéma privé pour les tables internes
- exposer uniquement un schéma `api` si nécessaire
- voire désactiver totalement la Data API si le backend gère tout

### 6.5 JSON brut et données sensibles

Vecteur:

- stockage brut de payloads tiers dans `JSONB`
- inclusion de PII, d'identifiants externes, de chemins de fichiers, voire de secrets par erreur

Impact:

- fuite de données métier sensibles
- rétention excessive
- difficulté à gouverner les accès

Mitigation:

- classifier chaque `payload_json` / `raw_payload_json`
- ne conserver que les champs utiles
- chiffrer si besoin
- définir une politique de rétention

### 6.6 Erreurs de permissions sur Storage

Vecteur:

- bucket public créé par facilité
- fichiers accessibles sans auth

Impact:

- fuite documentaire

Mitigation:

- bucket privé par défaut
- URLs signées si exposition temporaire
- contrôles par RLS côté storage

### 6.7 Fonctions SQL dangereuses

Vecteur:

- `SECURITY DEFINER` mal écrit
- `search_path` non verrouillé
- SQL dynamique futur côté backend ou fonctions

Impact:

- escalade de privilèges
- contournement de policies

Mitigation:

- fonctions privilégiées dans un schéma privé dédié
- `search_path` fixé explicitement
- revue stricte des fonctions admin

### 6.8 DoS logique

Vecteur:

- requêtes lourdes sur tables volumineuses
- API auto-générée laissée trop ouverte
- pagination absente
- imports bruts non bornés

Impact:

- saturation DB
- ralentissement général

Mitigation:

- pagination obligatoire
- indexes utiles
- quotas/rate limiting côté backend
- jobs asynchrones pour les imports

## 7. Ce que je pense de ton `config.toml`

Le fichier actuel est surtout la configuration locale standard Supabase. Il n'est pas "mauvais" en soi, mais il ne faut pas le lire comme une config de production.

Points à noter:

- `project_id = "src"` n'est pas parlant
- `schemas = ["public", "graphql_public"]` reste le comportement classique, mais ce n'est pas le plus prudent pour une app métier sensible
- `db.migrations.schema_paths = []` confirme que tu n'as pas encore mis en place un vrai flux de migrations
- `db.seed.enabled = true` mais `seed.sql` n'existe pas actuellement
- `db.network_restrictions` localement est permissif, ce qui est normal en dev, mais ne doit pas guider le design de prod
- `minimum_password_length = 6`, `password_requirements = ""`, `enable_confirmations = false`, `secure_password_change = false`, `mfa` désactivé: acceptable pour du local, pas comme posture cible

### Recommandation

Change au minimum:

- `project_id` vers quelque chose comme `aegis_local`
- la stratégie de schémas exposés quand tu passeras en vrai design d'API
- le workflow de migrations et de seed

## 8. Analyse du SQL actuel

Le vrai fichier de schéma actuel est:

`src/supabase/db/SCHEMA_VNEXT_CORE_PATCH.sql`

### 8.1 Ce qui est bien

- présence de clés primaires partout
- usage de UUID métier en plus des IDs numériques
- plusieurs contraintes `CHECK`
- quelques `UNIQUE`
- présence de tables dédiées par domaine métier

### 8.2 Ce qui pose problème structurellement

#### A. Aucune sécurité base native visible

Je n'ai trouvé:

- aucun `ENABLE ROW LEVEL SECURITY`
- aucun `CREATE POLICY`
- aucun `GRANT/REVOKE`
- aucune liaison explicite à `auth.users`

C'est le point de sécurité numéro un.

#### B. Le multi-tenant n'est pas encore sécurisé

Tu as un début de scoping avec `funds.id_org`, mais:

- toutes les tables n'embarquent pas clairement un `id_org`
- le contrôle d'accès devra faire beaucoup de joins
- ce sera fragile si tu relies ça uniquement au backend sans règles DB fortes

Pour une app hedge fund / risk / booking, il faut une stratégie claire:

- soit toutes les tables sensibles portent `id_org`
- soit tu assumes un modèle fondé sur `id_f`, mais alors les memberships utilisateur -> fonds doivent être propres et testées

#### C. Incohérences de nommage qui vont casser l'intégration

Le code frontend existant attend des noms comme:

- `trade_disc`
- `trade_disc_labels`

alors que le SQL définit:

- `trade_discr`
- `trade_labels`

Donc même sans parler cybersécurité, le design actuel n'est pas encore stabilisé entre front, base et backend.

#### D. Bug de schéma évident

Dans `counterparties`, tu déclares:

```sql
UNIQUE (code)
```

alors que la colonne `code` n'existe pas dans cette table.

Ça doit être corrigé avant toute base sérieuse.

#### E. Types et conventions encore instables

Exemples:

- `PayoutCurrency` en CamelCase/majuscule dans un schéma sinon en snake_case
- `t_date TEXT` alors que ça ressemble à une date
- certains champs devraient probablement être des enums de référence plutôt que du texte libre

Ça crée de la dette et ouvre la porte aux erreurs applicatives.

#### F. Tables snapshot incomplètes en intégrité relationnelle

Sur la partie SIMM / expiries:

- `id_simm_snapshot` n'a pas de FK visible vers `simm_snapshots`
- `id_exp_snapshot` n'a pas de FK visible vers `expiries_snapshots`
- `id_run` n'a pas de FK visible non plus

Ce n'est pas directement une faille, mais c'est un risque fort d'incohérence et de corruption logique.

#### G. Colonnes `raw_payload_json` / `payload_json`

Tu en as plusieurs:

- `trade_disc_premiums.payload_json`
- `trade_disc_instruments.payload_json`
- `trade_disc_settlements.payload_json`
- `simm_snapshot_rows.raw_payload_json`
- `expiries.raw_payload_json`

Sans classification et politique de conservation, ces colonnes vont devenir des "sacs à données" difficiles à sécuriser.

#### H. Traçabilité utilisateur insuffisante

Dans `trades`, tu as:

- `booked_by BIGINT`
- `last_modified_by BIGINT`

mais sans référence explicite à un vrai modèle utilisateur.

Je recommande un `UUID` référencé vers une table applicative adossée à `auth.users(id)`.

## 9. Ce que je ferais à ta place pour la base

### Décision d'architecture

Je partirais sur 4 schémas logiques:

```text
auth          -- géré par Supabase
app_private   -- tables métier non exposées directement
api           -- vues / fonctions exposables si besoin
audit         -- logs métiers et sécurité
```

### Principe

- les vraies tables métier vivent dans `app_private`
- le frontend ne touche pas `app_private` directement
- si tu veux exposer certaines lectures via Supabase client, tu exposes des vues contrôlées dans `api`
- sinon tu désactives carrément la Data API pour le métier et tu fais tout via backend

## 10. Ma recommandation backend "from scratch"

## Choix recommandé

Je te recommande:

- `Supabase` pour `Auth + Postgres + éventuellement Storage`
- `FastAPI` pour le backend métier
- `psycopg` ou `SQLAlchemy 2.x` côté backend pour les accès DB
- migrations SQL sous `supabase/migrations/`

### Pourquoi FastAPI ici

- ton projet a déjà une base Python
- ton domaine est très data/métier/finance
- Python sera plus naturel si tu relies des librairies quant, fichiers Excel, workflows de calcul, imports et traitements

### Principe de sécurité backend

Le frontend:

- récupère une session Supabase Auth
- envoie le JWT au backend

Le backend:

- vérifie le JWT Supabase
- résout l'utilisateur applicatif
- charge ses memberships org/fund/roles
- applique les autorisations métier
- exécute les transactions de booking, validation, imports, exports

### Ce que le frontend ne doit plus faire

- `insert()` direct dans `trade_disc`, `trade_disc_legs`, etc.
- `select('*')` libre sur les tables métier
- accès direct aux tables sensibles de contrôle, recap, positions, risque

## 11. Backend cible: responsabilités

### Ce que Supabase doit gérer

- identité
- sessions
- base Postgres
- éventuellement fichiers

### Ce que le backend doit gérer

- autorisation métier
- transactions complexes multi-tables
- validation stricte des payloads
- intégrations externes
- journalisation d'audit
- rate limiting
- anti-IDOR
- règles hedge fund / trading / recap / validation

## 12. Modèle de sécurité cible

### Tables minimales à ajouter très tôt

- `app_users`
- `organisations`
- `memberships`
- `membership_roles`
- `fund_memberships`
- `audit_log`
- `ingestion_runs`

### Exemple de relation d'identité

```text
auth.users.id
  -> app_users.auth_user_id
  -> memberships.user_id
  -> memberships.org_id / fund_id / role
```

### Avantage

Tu ne relies jamais les permissions à un simple header client ou à une variable front. Tu relies les droits à un utilisateur authentifié et à ses memberships en base.

## 13. Workflow recommandé de développement base

### Workflow sain

1. écrire une migration SQL
2. lancer Supabase local
3. appliquer la migration
4. lancer les tests DB
5. lancer le lint DB
6. générer les types
7. seulement ensuite brancher le backend

### Commandes utiles à intégrer dans le workflow

- `supabase start`
- `supabase migration new <name>`
- `supabase db reset`
- `supabase db lint`
- `supabase test db`
- `supabase gen types`

## 14. Ce que je te recommande de faire maintenant

### Garde

- Supabase comme moteur de base et auth
- le SQL actuel comme matière première fonctionnelle

### Renomme

- `src/supabase/` -> `supabase/`
- `SCHEMA_VNEXT_CORE_PATCH.sql` -> première migration propre dans `supabase/migrations/`

### Abandonne

- `tables.sql`, `insert.sql`, `delete.sql` comme stratégie principale

### Refais avant toute implémentation métier

- modèle utilisateur / memberships / organisations
- RLS
- séparation `app_private` / `api`
- backend transactionnel

## 15. Plan concret par étapes

### Étape 1. Assainir le repo

- déplacer `src/supabase` vers `supabase`
- créer `supabase/migrations`
- créer `supabase/seed.sql`
- créer `supabase/tests`

### Étape 2. Stabiliser le schéma

- corriger les incohérences de noms
- corriger les FKs manquantes
- corriger `counterparties`
- harmoniser les types

### Étape 3. Sécurité DB

- créer tables users/memberships
- activer RLS
- écrire policies
- écrire tests RLS

### Étape 4. Backend minimal

- auth middleware JWT Supabase
- endpoint `GET /me`
- endpoints lecture références
- endpoint transactionnel de booking

### Étape 5. Frontend

- retirer les accès directs aux tables sensibles
- conserver au pire Supabase client pour auth et quelques lectures non sensibles

## 16. Verdict

Oui, garder Supabase est une bonne idée.

Mais:

- pas comme simple "base exposée au navigateur"
- pas avec des tables métier sensibles en `public` sans RLS
- pas avec un pseudo-workflow basé sur `tables.sql` / `insert.sql` / `delete.sql`

Pour Aegis, la bonne direction est:

- `Supabase` comme plateforme de données/auth
- `backend applicatif dédié`
- `migrations versionnées`
- `RLS + memberships + schéma privé`

## 17. Sources officielles utiles

- Supabase CLI `supabase init`: https://supabase.com/docs/reference/cli/supabase-migration-new
- Local development with schema migrations: https://supabase.com/docs/guides/local-development/overview
- Hardening the Data API: https://supabase.com/docs/guides/database/hardening-data-api
- Using custom schemas: https://supabase.com/docs/guides/api/using-custom-schemas
- Testing and linting: https://supabase.com/docs/guides/local-development/cli/testing-and-linting
- Column Level Security: https://supabase.com/docs/guides/database/postgres/column-level-security

