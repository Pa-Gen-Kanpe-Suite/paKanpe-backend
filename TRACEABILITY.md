# Matrice de traçabilité

| Besoin | Backend | Frontend | Test principal |
| --- | --- | --- | --- |
| Authentification JWT/RBAC | `/api/v1/auth/*` | connexion, inscription, gardes de rôle | `test_auth.py` |
| Ticket numérique | `POST /client/tickets` | tableau client | `test_ticket_lifecycle.py` |
| Ticket physique | `POST /agent/tickets/physical` | tableau agent | `test_agent_ticket.py` |
| Refus du doublon | index partiel + service transactionnel | message 409 | `test_double_booking.py` |
| Position et estimation | `GET /queues/position/{code}` | suivi avec actualisation | `test_queue_service.py` |
| Appel FIFO | `POST /cashier/counters/{id}/next-ticket` | tableau caissier | `test_ticket_lifecycle.py` |
| Absence | `PATCH /cashier/tickets/{id}/no-show` | action temporisée | `test_ticket_lifecycle.py` |
| Pause guichet | `PATCH /cashier/counters/{id}/status` | tableau caissier | `test_counter.py` |
| Statistiques | `GET /admin/statistics/overview` | tableau admin | `test_statistics.py` |
| Temps réel | `/ws/queue` et polling de repli | suivi/affichage public | `test_websocket.py` |

