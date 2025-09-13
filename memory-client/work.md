                                                                            
Voici la liste des endpoints que le SDK Python (memory_client, clone de mem0ai)       
appelle. Les chemins sont relatifs à host (par défaut Cloud: https://api.mem0.ai). Les
en‑têtes attendus incluent Authorization: Token <API_KEY> et Mem0-User-ID.   

On doit modifier ce SDK pour notre propre memory-orchestrator service qui est installé devant le serveur mem0.
                                                                                      
Santé                                                                                 

A RETIRER                                                                                      
- GET: /v1/ping/ — valide la clé et renseigne org_id/project_id.                      
                                                                                      
Memories                                                                                          

A MODIFIER SELON NOTRE PROPRE SERVICE
- GET: /memories/ — liste/filtre des mémoires (version typique: v1).        
- POST: /memories/ — crée des mémoires.                                     
- POST: /memories/search/ — recherche des mémoires.                         
- GET: /memories/{memory_id}/ — récupère une mémoire.                              
- GET: /memories/{memory_id}/history/ — historique d’une mémoire.                  
- PUT: /memories/{memory_id}/ — met à jour une mémoire.                            
- DELETE: /memories/{memory_id}/ — supprime une mémoire.                           
- DELETE: /memories/ — suppression en masse (par filtres).                         

A RETIRER
- PUT: /batch/ — opérations batch sur des mémoires.                                
                                                                                      
Entities                                                                              

A RETIRER                                                                                      
- GET: /v1/entities/ — récupère les entités.                                          
- DELETE: /v2/entities/{type}/{name}/ — supprime une entité (endpoint v2).            
                                                                                      
Exports & Résumés                                                                     

A RETIRER                                                                                   
- POST: /v1/exports/ — lance un export.                                               
- POST: /v1/exports/get/ — récupère un export.                                        
- POST: /v1/summary/ — génère un résumé.                                              
                                                                                      
Feedback                                                                              

A RETIRER                                                                                     
- POST: /v1/feedback/ — envoie un feedback sur une mémoire.                           
                                                                                      
Webhooks                                                                              

A RETIRER                                                                                
- GET: api/v1/webhooks/projects/{project_id}/ — liste les webhooks d’un projet.       
- POST: api/v1/webhooks/projects/{project_id}/ — crée un webhook.                     
- PUT: api/v1/webhooks/{webhook_id}/ — met à jour un webhook.                         
- DELETE: api/v1/webhooks/{webhook_id}/ — supprime un webhook.                        
                                                                                      
Orgs & Projets

A RETIRER                                                                                      
- POST: /api/v1/orgs/organizations/{org_id}/projects/ — crée un projet.               
- GET: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/ — détail d’un       
projet.                                                                               
- DELETE: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/ — supprime un    
projet.                                                                               
- GET: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/members/ — liste     
des membres.                                                                          
- POST: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/members/ — ajoute   
un membre.                                                                            
- PUT: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/members/ — change le 
rôle d’un membre.
- DELETE: /api/v1/orgs/organizations/{org_id}/projects/{project_id}/members/ — retire 
un membre.

Notes

A RETIRER GESTION DE VERSION
- version est passé par le client (ex: v1). Certains endpoints “Entities” utilisent   
v2.
- org_id/project_id peuvent être requis (soit envoyés en params, soit déduits par /v1/
ping/ côté Cloud).
- Le serveur FastAPI local de ce repo n’expose pas ces routes Cloud; utilisez host    
vers l’API Cloud pour ce SDK, ou implémentez des endpoints compatibles côté serveur   
si nécessaire.
