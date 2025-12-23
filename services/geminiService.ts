import { GoogleGenAI, Type } from "@google/genai";
import { LegalStage, AttachedFile, Prestation } from "../types";
import { KNOWLEDGE_BASE } from "./knowledgeBase";

// Helper to get the AI instance
const getAI = () => {
    const apiKey = process.env.API_KEY;
    if (!apiKey) {
        throw new Error("API Key is missing. Please set the API_KEY environment variable.");
    }
    return new GoogleGenAI({ apiKey });
};

// Convert file to compatible generative part
const fileToPart = (file: AttachedFile) => {
    return {
        inlineData: {
            data: file.base64,
            mimeType: file.mimeType
        },
    };
};

/**
 * Step 1: Analyze the case to determine the legal stage, the prestations, and if they are accepted.
 */
export const detectCaseStage = async (
    description: string,
    files: AttachedFile[]
): Promise<{ stage: LegalStage, prestations: Prestation[] }> => {
    const ai = getAI();
    const model = 'gemini-2.5-flash';

    const parts: any[] = [];
    
    // Add all files to the prompt parts
    files.forEach(file => {
        parts.push(fileToPart(file));
    });
    
    if (files.length > 0) {
        parts.push({ text: "Documents fournis par le client ci-dessus." });
    }

    parts.push({ text: `
    CONTEXTE:
    Tu es avocat spécialisé en droit administratif (CAF). 
    Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.
    Écris à la première personne comme si c'était moi, sous forme de paragraphes clairs, évite le jargon, pas plus d'un niveau de bullet-points. Ton style est clair, concis, engageant, et accessible pour le grand public.
    
    BASE DE CONNAISSANCES DU CABINET (Ce que nous traitons ou non):
    ${KNOWLEDGE_BASE}
    
    DESCRIPTION DU CAS PAR LE CLIENT:
    "${description}"

    TÂCHE:
    Analysez les documents et la description pour :
    1. Identifier l'étape précise de la procédure (stage).
    2. Identifier TOUTES les prestations concernées (RSA, APL, AAH, etc.). Il peut y en avoir plusieurs.
    3. Pour chaque prestation, déterminer si le cabinet traite ce type de recours selon la Base de Connaissances (isAccepted).

    RÈGLES DE CLASSIFICATION (STAGE):
    1. CONTROL : Lettre de fin de contrôle, Procédure contradictoire, invitation à observations. Pas d'indu formel.
    2. RAPO : Notification d'indu, révision de droits, délai de 2 mois ouvert pour CRA/Président CD.
    3. LITIGATION : RAPO rejeté (explicite ou implicite), saisine Tribunal Administratif.

    RÈGLES D'ACCEPTATION (isAccepted):
    - Regardez la colonne "Recours dont traite le cabinet" dans la Base de Connaissances.
    - ✅ = Accepté (RSA, Prime d'activité, APL, etc.).
    - ❌ = Refusé (Handicap, AAH, AEEH, Tribunal Judiciaire, etc.).

    Retournez uniquement le JSON suivant :
    { 
      "stage": "CONTROL" | "RAPO" | "LITIGATION",
      "prestations": [
        { "name": "Nom de la prestation", "isAccepted": true | false }
      ]
    }
    `});

    try {
        const response = await ai.models.generateContent({
            model: model,
            contents: { parts },
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        stage: { type: Type.STRING, enum: [LegalStage.CONTROL, LegalStage.RAPO, LegalStage.LITIGATION] },
                        prestations: { 
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    name: { type: Type.STRING },
                                    isAccepted: { type: Type.BOOLEAN }
                                },
                                required: ["name", "isAccepted"]
                            }
                        }
                    },
                    required: ["stage", "prestations"]
                }
            }
        });
        
        const json = JSON.parse(response.text || "{}");
        return {
            stage: json.stage as LegalStage || LegalStage.RAPO,
            prestations: json.prestations || [{ name: "Non identifiée", isAccepted: true }]
        };

    } catch (error) {
        console.error("Error detecting stage:", error);
        return { 
            stage: LegalStage.RAPO, 
            prestations: [{ name: "Erreur détection", isAccepted: true }] 
        };
    }
};

/**
 * Step 2: Get the prompt templates based on the stage.
 */
export const getPromptTemplates = (stage: LegalStage, clientName: string, description: string) => {
    
    const contextHeader = `
CONTEXTE:
Tu es avocat spécialisé en droit administratif (CAF). 
Tu rédiges pour le compte de Maître Ilan BRUN-VARGAS.
Écris à la première personne comme si c'était moi, sous forme de paragraphes clairs, évite le jargon, pas plus d'un niveau de bullet-points.

RÉFÉRENCE JURIDIQUE INTERNE (BASE DE CONNAISSANCES):
${KNOWLEDGE_BASE}
Utilise cette base pour citer les bons articles de loi et vérifier les délais/procédures applicables.

STYLE & FORMATTAGE (IMPÉRATIF):
- Format APA Strict : Police standard, double interligne.
- AUCUN MARKDOWN (Pas de gras **, pas de titres ##, pas d'italique).
- TEXTE BRUT uniquement.
- TITRES DE SECTIONS EN MAJUSCULES (ex: OBJET, FAITS, DISCUSSION).
- Ton : structuré, clair, concis, engageant, et accessible pour le grand public.

DESCRIPTION CLIENT: "${description}"
NOM CLIENT: ${clientName || "[Nom du Client]"}
`;

    // --- EMAIL PROMPTS ---
    let emailInstructions = "";

    if (stage === LegalStage.CONTROL) {
        emailInstructions = `
${contextHeader}

TÂCHE : Rédige un email au client couvrant ces points (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION.
2. RAPPEL DE LA SITUATION TELLE QUE JE LA COMPRENDS : Contrôle CAF effectué, réception courrier "procédure contradictoire", incohérences/constatations soulevées.
3. RECOURS : Expliquer qu'il y a un délai de 10 jours pour les observations un fois le courrier "procédure contradictoire" reçu. Prochaine étape = décision de la Caf sur les constatations et éventuelles observations (indu).
4. PROCHAINE ÉTAPE : Inviter le client à recontacter dès réception de la décision de la Caf pour renseigner sur possiblités de contestation.
Salutations distinguées.
`;
    } else if (stage === LegalStage.RAPO) {
        emailInstructions = `
${contextHeader}

TÂCHE : Rédige un email au client couvrant ces points (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION et récapitulatif des sommes réclamées.
2. OBSERVATIONS SUR LE BIEN-FONDÉ : Identifier pourquoi la CAF réclame (séjour, ressources), et les eventuelles réponses/arguments factuels fournis par le client.
3. VOIES DE RECOURS : Expliquer les destinataires différents pour les prestations concernées (Président CD pour RSA, Directeur CAF pour APL, CRA pour Prime d'activité). Délai en principe de 2 mois. Expliquer l'envoi en LRAR.
4. REMISE DE DETTE : Possible en parallèle, indépendant du bien-fondé. Repose uniquement sur situation financière et bonne foi (indisponible si l'administration retient la fraude, il faut alors la contester au préalable devant le tribunal administratif).
5. PROPOSITION D'ACCOMPAGNEMENT : Peut l'accompagner et rédiger RAPO(s) pour le client. Honoraires peuvent être pris en charge par assurance protection juridique (généralement incluse avec leur assurance habitation), ou peut prendre les honoraires à leure charge. L'aide juridictionnelle n'est pas dispobile pour cette étape du recours. Alternativement, je pourrai lui proposer gratuitement un modèle de recours duquel partir.
6. ACTION : Inviter à indiquer ce que souhaite faire (accompagnement ou pas) et que peut joindre les Conditions Générales/Contrat de son assurance afin que renseigne sur couvert ou non pour ce type de litiges.
Salutations distinguées.
`;
    } else { // LITIGATION
        emailInstructions = `
${contextHeader}

TÂCHE : Rédige un email au client pour la phase contentieuse (à la 1ère personne) :
1. ACCUSÉ DE RÉCEPTION. Le RAPO a été rejeté (ou silence gardé).
2. SAISINE DU TRIBUNAL ADMINISTRATIF : C'est la prochaine étape. Délai de 2 mois.
3. PROCÉDURE : Essentiellement écrite, via Télérecours Citoyens.
4. PROPOSITION D'ACCOMPAGNEMENT. Financement des honoraires. Devant le tribunal administratif, la procédure est essentiellement écrite, et vous pouvez déposer votre recours vous-même via la plateforme en ligne Télérecours Citoyens. Un avocat n'est pas obligatoire, mais si vous le souhaitez, je peux prendre votre dossier. Il existe plusieurs solutions pour le financement : • Prendre les honoraires à votre charge personnelle. • Demander l'aide juridictionnelle si vos ressources sont modestes (vous devez préparer le dossier et le déposer au bureau d'aide juridictionnelle). • Utiliser votre assurance habitation (qui comporte une clause de protection juridique). C'est souvent la voie préférée et la plus rapide. Vous pouvez m'envoyer une copie de votre contrat d'assurance habitation pour que je vous confirme les garanties et contacte l'assureur si nécessaire.
5. DEMANDE DE CONFIRMATION du souhait de poursuivre ensemble ou non le contentieux. Peut me fournir les Conditions Générales/Contrat de son assurance afin que renseigne sur couvert ou non pour ce type de litiges.
Salutations distinguées.
`;
    }

    // --- APPEAL (RAPO) PROMPTS ---
    let appealInstructions = "";
    
    if (stage === LegalStage.CONTROL) {
        appealInstructions = `
${contextHeader}
TÂCHE : Rédige une note succincte de "OBSERVATIONS SUITE À PROCÉDURE CONTRADICTOIRE". Redige comme si c'etait le client, sans jargon juridique et sans mots inutiles/tournures lourdes. En language "FALC", facile a lire et a comprendre.
Structure :
- EN-TÊTE (Client)
- OBJET : OBSERVATIONS SUITE AU CONTRÔLE N°[Numéro]
- FAITS : Chronologie simple.
- RÉPONSE AUX CONSTATATIONS : Argumentation factuelle contre les incohérences (résidence, isolement, ressources, etc.).
- CONCLUSION : Demande d'abandon des constatations et de la procédure de rectification.
`;
    } else if (stage === LegalStage.RAPO) {
        appealInstructions = `
${contextHeader}
TÂCHE : Rédige un "RECOURS ADMINISTRATIF PRÉALABLE OBLIGATOIRE" (RAPO).
Destinataire : Président de la Commission de Recours Amiable (ou Président Conseil Départemental) selon la prestation identifiée dans la Base de Connaissances.
# Rôle et Objectif
Tu es un expert juridique assistant un avocat en droit administratif. Ta tâche est de rédiger un projet de Recours Administratif Préalable Obligatoire (RAPO) contre un indu de prestation sociale.

# Ton et Style (Crucial)
1.  **Posture d'Allié :** Adopte la posture d'un "allié" ou d'un rapporteur public. Tu ne cherches pas le conflit, mais tu aides l'administration à "rendre la bonne décision" en éclairant les faits. Le ton est courtois, constructif, mais ferme sur le droit.
2.  **Langage FALC :** Utilise le "Facile à Lire et à Comprendre". Bannis le jargon juridique inutile. Fais des phrases courtes (Sujet-Verbe-Complément). Le destinataire est un agent administratif surchargé : facilite-lui la lecture. Sois "helpful".
3.  **Clarté :** Va droit au but. Sois percutant.

# Instructions de Formatage (Style APA adapté)
* Utilise une hiérarchie claire avec des titres numérotés.
* Police standard et aérée.
* Respecte scrupuleusement la structure ci-dessous.

# Logique Juridique
* **Si RSA :** Le destinataire est le Président du Conseil Départemental. Le recours est suspensif (L.262-46 CASF).
* **Si APL/Prime d'activité :** Le destinataire est la Commission de Recours Amiable (CRA). Le recours n'est pas suspensif par défaut (demander la suspension).

# Structure du Courrier (Template à suivre)

[Insérer Nom Prénom Client]
[Adresse Client]
Numéro allocataire : [Numéro]

[Insérer Destinataire compétent identifié selon les documents]
[Adresse du service]

[Ville], le [Date du jour]
Par recommandé avec accusé de réception (LRAR)

Objet : Recours administratif contre un indu de [Nom de la prestation] - [Montant] euros

Madame, Monsieur [le Président / les membres de la Commission],

Par courrier du [Date décision], vous m'avez informé d'un trop-perçu de [Montant] euros concernant [Nom de la prestation]. Vous justifiez cette décision par [Résumer très brièvement le motif de l'administration].

**1. Demande d'annulation**
Je conteste cette décision car elle repose sur une erreur d'appréciation.

[ICI, insérer l'argumentation factuelle basée sur les documents fournis. Explique le "cas positif" du client. Sois clair : "J'habite bien en France", "Ces revenus ne doivent pas être comptés", etc. Utilise des puces si plusieurs arguments.]

Au vu de ces éléments, je vous prie d'annuler cet indu et de rétablir mes droits.

**2. Demande de remise de dette (Subsidiaire)**
Si vous maintenez l'indu malgré mes explications, je sollicite une remise totale de la dette.
Ma situation est très précaire : [Résumer situation financière : revenus, charges, reste à vivre]. Je suis de bonne foi et cette dette aggraverait dramatiquement ma situation.

**3. Demande de transmission du rapport de contrôle**
Conformément aux articles L.311-1 et L.300-2 du CRPA, je demande la copie intégrale du rapport de contrôle ou d'enquête ayant motivé votre décision.

**4. Suspension du recouvrement**
[SI RSA, insérer :] Ce recours est suspensif (art. L.262-46 du CASF). Merci de bloquer toute retenue sur mes allocations en attendant la décision.
[SI AUTRE PRESTATION, insérer :] Bien que ce recours ne soit pas suspensif de plein droit, je vous demande de suspendre le recouvrement dans l'attente de la décision, au vu de ma fragilité financière.

**Sans réponse favorable dans un délai de deux mois, je poursuivrai mon recours devant le tribunal administratif.**

Dans l'attente de votre réexamen, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

______________________
(Signature)

Pièces jointes : Copie de la décision contestée, [Lister les preuves mentionnées dans l'argumentation]
`;
    } else { // LITIGATION
        appealInstructions = `
${contextHeader}
# RÔLE ET OBJECTIF
Tu agis en tant qu'avocat expert en droit administratif français, spécialisé dans le contentieux des prestations sociales qui relevant du tribunal administrative uniquement (RSA, APL, Prime d'activité, etc.). Ta mission est de rédiger un projet de **Requête Introductive d'Instance** devant le Tribunal Administratif pour contester un indu de prestation(s) sociale(s). Ne couvre que les prestations qui ont fait l'objet d'un même recours administratif préalable devant le même auteur.

# DOCUMENTS D'ENTRÉE
Je te fournis un tableau de connaissances sous forme de questions reponses juridiques. Je te fournis aussi les documents de l'affaire (lettres de notification d'indu, décision sur RAPO, justificatifs de ressources, courriers du client, etc). Analyse-les minutieusement pour extraire :
1. La chronologie exacte des faits.
2. Les motifs de droit et de fait invoqués par l'administration (CAF, Département)
3. Les arguments de bonne foi et la situation financière du requérant.

# STYLE ET TONALITÉ : "L'ALLIÉ DU JUGE"
Ton style de rédaction est critique pour ce dossier. Tu dois respecter les contraintes suivantes :
1.  **Approche FALC (Facile à Lire et à Comprendre) :**
    * Utilise des phrases courtes (Sujet - Verbe - Complément).
    * Bannis le jargon juridique archaïque ou les formules latines inutiles.
    * Privilégie la voix active.
    * L'objectif est que n'importe quel citoyen puisse comprendre, mais que le raisonnement juridique soit inattaquable.
2.  **Posture du "Rapporteur Public" :**
    * Ne sois pas agressif ou inutilement polémique. Sois pédagogique.
    * Adopte une logique syllogistique implacable (Majeure, Mineure, Conclusion).
    * Ton but est de faciliter le travail de rédaction du jugement par le magistrat. Présente les faits et le droit de manière si claire qu'il pourrait copier-coller tes paragraphes dans sa décision.

# FORMATTING (STYLE APA)
* Texte en double interligne.
* Police lisible (type Times New Roman ou Arial, taille 12).
* Marges de 2,54 cm (1 pouce).
* Titres et sous-titres clairs et hiérarchisés.
* Longueur cible : Environ 10 à 12 pages, en fonction de la densité des arguments.

# STRUCTURE DE LA REQUÊTE
Organise la requête selon le plan suivant :

## I. FAITS ET PROCÉDURE
Rédige un récit chronologique, neutre et factuel.
* Date d'ouverture des droits.
* Date et montant de la notification de l'indu.
* Détails du Recours Administratif Préalable Obligatoire (RAPO) : date d'envoi et date de la décision de rejet (implicite ou explicite).
* *Conseil : Mets en évidence les incohérences de l'administration ici si elles existent.*

## II. RECEVABILITÉ
Démontre brièvement que la requête est recevable (compétence du tribunal, respect du délai de recours de 2 mois, existence de la décision attaquée).

## III. DISCUSSION
Divise cette partie en deux sous-sections claires.

### A. Sur la régularité externe (Légalité externe)
* Vérifie la motivation de la décision (est-elle assez précise en fait et en droit ?).
* Vérifie la compétence de l'auteur de l'acte (signataire).
* Vérifie le respect de la procédure contradictoire (le client a-t-il pu présenter ses observations ?).
* Verifie le respect des règles de procedure (consultation pour avis de la commission de recours amiable lorsque c'est exigé ? Preuve de l'habilitation, agrément et assermentation de l'agent de contrôle ?)

### B. Sur le bien-fondé de l'indu (Légalité interne)
C'est le cœur de l'argumentation. Analyse les points suivants et utilise ceux qui sont pertinents :
1.  **L'erreur de l'administration :** Si l'indu résulte d'une erreur de la CAF/Département alors que le client a tout déclaré.
2.  **La prescription :** Vérifie si la période réclamée dépasse le délai légal (généralement 2 ans pour CAF/RSA, sauf fraude où cela deviant cinq ans).
3.  **La nature des ressources :** L'administration a-t-elle mal qualifié les revenus (ex: libéralités vs revenus, épargne vs capitaux placés) ?
4. **La presence hors de France moins de 92 jours par année, uniquement si elle est invoquée comme fondement de la décision par l'administration.
5.  **La bonne foi :** Démontre l'absence d'intention frauduleuse.

### C. (Subsidiairement) Sur la remise gracieuse
Si l'indu est fondé en droit, argumente pour une remise totale ou partielle basée sur :
* La précarité de la situation (reste à vivre insuffisant). Nous joindrons des justificatifs de ses ressources et charges (factures, etc.).
* La bonne foi du requérant.
* Les conséquences disproportionnées du remboursement sur la vie du foyer.

## IV. CONCLUSIONS (DISPOSITIF)
Liste formellement ce que nous demandons au tribunal :
1.  Annuler la décision du [Date] rejetant le RAPO.
2.  Décharger M./Mme [Nom] de la somme de [Montant].
3.  Enjoindre à l'administration de rembourser les sommes déjà prélevées.
4. Subsidiairement, la remise totale de la dette ou son adéquation au budget mensuel et à l'interêt public de maintenir le client dans l'autonomie.
4.  Condamner l'administration à verser [Montant, ex: 1500 euros] au titre de l'article L.761-1 du CJA.
`;
    }

    return {
        emailPrompt: emailInstructions.trim(),
        appealPrompt: appealInstructions.trim()
    };
};

/**
 * Step 3: Execute the generation based on a specific prompt text.
 */
export const generateSingleDraft = async (
    prompt: string,
    files: AttachedFile[]
): Promise<string> => {
    const ai = getAI();
    const model = 'gemini-2.5-flash';

    const parts: any[] = [];
    
    // Include all files for grounding
    files.forEach(file => {
        parts.push(fileToPart(file));
    });
    
    if (files.length > 0) {
        parts.push({ text: "RÉFÉRENCE : Documents du dossier (à utiliser pour extraire dates, montants, motifs, etc)." });
    }

    // Prompt includes the knowledge base implicitly because it was passed in the 'prompt' string by getPromptTemplates
    // BUT, we ensure the 'prompt' passed here is what comes from the UI (which originated from getPromptTemplates).
    parts.push({ text: prompt });

    try {
        const response = await ai.models.generateContent({
            model: model,
            contents: { parts }
        });
        return response.text || "";
    } catch (error) {
        console.error("Error generating single draft:", error);
        throw error;
    }
};

// Helper to read file as base64
export const readFileAsBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            const result = reader.result as string;
            const base64 = result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = error => reject(error);
    });
};