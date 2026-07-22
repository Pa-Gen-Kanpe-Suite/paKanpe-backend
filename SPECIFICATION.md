# Spécification consolidée — MVP PA GEN KANPE

## Périmètre

Le MVP couvre une banque (UNIBANK), une agence, une file FIFO unique et quatre rôles : client, agent d'accueil, caissier et administrateur. Les tickets numériques et physiques utilisent exactement la même file.

## Décisions d'arbitrage

Les documents ne sont pas toujours cohérents. Les décisions suivantes rendent le produit déterministe :

1. Le PRD Product Management prévaut sur les propositions exploratoires des autres équipes.
2. Un client absent après cinq minutes de grâce passe à `ABSENT`, état terminal. Il doit reprendre un ticket. La file secondaire et le statut `LATE` sont reportés.
3. Un client peut annuler uniquement un ticket `WAITING`.
4. La clôture d'un ticket appelle automatiquement le suivant sur le même guichet par défaut. Le comportement est désactivable par requête.
5. L'ordre FIFO est basé sur `created_at`, puis sur l'identifiant. La sélection du prochain ticket utilise un verrou transactionnel pour empêcher deux guichets d'appeler le même ticket.
6. Un seul ticket actif (`WAITING`, `CALLED`, `IN_PROGRESS`) est permis par client.
7. Un guichet ne peut avoir qu'un ticket `CALLED` ou `IN_PROGRESS` à la fois.
8. Le temps d'attente utilise la moyenne des vingt derniers tickets terminés, avec cinq minutes par défaut, divisée par le nombre de guichets ouverts.
9. Les notifications du MVP sont internes à l'application. Les SMS et notifications push externes restent hors périmètre.
10. Les statistiques sont calculées depuis les tickets, sans table d'agrégats susceptible de se désynchroniser.

## États

| État | Description | Transitions permises |
| --- | --- | --- |
| `WAITING` | Dans la file | `CALLED`, `CANCELLED` |
| `CALLED` | Appelé à un guichet | `IN_PROGRESS`, `ABSENT` |
| `IN_PROGRESS` | Service en cours | `CLOSED` |
| `CLOSED` | Service terminé | Terminal |
| `ABSENT` | Non présenté après la grâce | Terminal |
| `CANCELLED` | Annulé avant appel | Terminal |

## Critères d'acceptation essentiels

- Deux créations simultanées ne peuvent pas produire deux tickets actifs pour un client.
- Deux caissiers ne peuvent pas appeler le même ticket.
- Un ticket physique et un ticket numérique sont ordonnés ensemble.
- La position, le temps estimé et l'affichage public se mettent à jour après chaque transition.
- Chaque endpoint protégé vérifie le JWT et le rôle.
- Les erreurs de validation utilisent des codes HTTP explicites sans exposer de trace interne.
- Les interfaces client tiennent en trois étapes : accueil, choix du service, suivi.
- Les interfaces fonctionnent sur smartphone, tablette et ordinateur.

## Hors périmètre MVP

Multi-banques, multi-agences, paiement, réservation planifiée, IA prédictive, SMS, historique avancé, file secondaire et mode hors ligne complet.

