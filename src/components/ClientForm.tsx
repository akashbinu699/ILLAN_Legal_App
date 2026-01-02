import React, { useState, useRef } from 'react';
import { FormInput } from './FormInput';
import type { FormErrors, ClientSubmission, AttachedFile } from '../types';
import { readFileAsBase64 } from '../utils/fileUtils';

interface ClientFormProps {
    onSubmit: (data: Omit<ClientSubmission, 'id' | 'status' | 'submittedAt' | 'stage' | 'prestations' | 'generatedEmailDraft' | 'generatedAppealDraft' | 'emailPrompt' | 'appealPrompt'>) => Promise<void>;
}

export const ClientForm: React.FC<ClientFormProps> = ({ onSubmit }) => {
    const [formData, setFormData] = useState({
        email: '',
        phone: '',
        description: '',
        files: [] as File[],
    });

    const [agreedType, setAgreedType] = useState(false);
    const [agreedPrivacy, setAgreedPrivacy] = useState(false);
    const [errors, setErrors] = useState<FormErrors>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (errors[name as keyof FormErrors]) {
            setErrors((prev: FormErrors) => ({ ...prev, [name]: undefined }));
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            // Convert FileList to Array and append
            const newFiles = Array.from(e.target.files);
            setFormData(prev => ({ ...prev, files: [...prev.files, ...newFiles] }));
            setErrors((prev: FormErrors) => ({ ...prev, file: undefined }));
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const newFiles = Array.from(e.dataTransfer.files);
            setFormData(prev => ({ ...prev, files: [...prev.files, ...newFiles] }));
            setErrors((prev: FormErrors) => ({ ...prev, file: undefined }));
        }
    };

    const removeFile = (index: number, e: React.MouseEvent) => {
        e.stopPropagation();
        setFormData(prev => ({
            ...prev,
            files: prev.files.filter((_, i) => i !== index)
        }));
    };

    const validateEmail = (email: string): boolean => {
        // Basic email validation regex - more lenient
        // Allows: user@domain.com, user.name@domain.co.uk, etc.
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const trimmedEmail = email.trim();
        if (!trimmedEmail) return false;
        return emailRegex.test(trimmedEmail);
    };

    const validate = () => {
        const newErrors: FormErrors = {};
        const trimmedEmail = formData.email.trim();

        if (!trimmedEmail) {
            newErrors.email = "L'email est requis";
        } else if (!validateEmail(trimmedEmail)) {
            newErrors.email = "Veuillez entrer une adresse email valide (ex: nom@exemple.com)";
        }
        if (!formData.phone.trim()) newErrors.phone = "Le téléphone est requis";
        if (formData.files.length === 0) newErrors.file = "Au moins un document de la CAF est requis";

        setErrors(newErrors);
        const isValid = Object.keys(newErrors).length === 0 && agreedType && agreedPrivacy;

        // Show alert if validation fails with specific reason
        if (!isValid) {
            if (!agreedType) {
                alert("Please confirm that your request concerns RSA, Activity Bonus, or Housing Assistance.");
            } else if (!agreedPrivacy) {
                alert("Please accept the privacy policy.");
            } else if (Object.keys(newErrors).length > 0) {
                const errorMessages = Object.values(newErrors).filter(Boolean).join('\n');
                alert(`Please correct the following errors:\n${errorMessages}`);
            }
        }

        return isValid;
    };

    const handleSubmit = async () => {
        console.log("Submit button clicked");
        console.log("Form data:", formData);
        console.log("Agreed type:", agreedType, "Agreed privacy:", agreedPrivacy);

        const isValid = validate();
        console.log("Validation result:", isValid);
        console.log("Errors:", errors);

        if (!isValid) {
            console.log("Validation failed, not submitting");
            return;
        }

        setIsSubmitting(true);
        try {
            console.log("Processing files...");
            // Process all files
            const processedFiles: AttachedFile[] = [];
            for (const file of formData.files) {
                const base64 = await readFileAsBase64(file);
                processedFiles.push({
                    name: file.name,
                    mimeType: file.type,
                    base64: base64
                });
            }

            console.log("Calling onSubmit with:", {
                email: formData.email,
                phone: formData.phone,
                description: formData.description,
                filesCount: processedFiles.length
            });

            await onSubmit({
                email: formData.email,
                phone: formData.phone,
                description: formData.description,
                files: processedFiles
            });
            console.log("Submission successful");
            // Reset form could go here, but usually we redirect to a thank you page
        } catch (e) {
            console.error("Submission error:", e);
            const errorMessage = e instanceof Error ? e.message : "Une erreur est survenue lors de l'envoi.";
            alert(`Erreur: ${errorMessage}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto bg-white p-8 md:p-12 shadow-sm min-h-screen">

            <section className="mb-10">
                <h2 className="text-xl font-normal text-brand-dark mb-6">1. Mes coordonnées</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormInput
                        label="Email"
                        name="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        error={errors.email}
                    />
                    <FormInput
                        label="Téléphone portable"
                        name="phone"
                        required
                        value={formData.phone}
                        onChange={handleInputChange}
                        error={errors.phone}
                    />
                </div>
            </section>

            <section className="mb-10">
                <h2 className="text-xl font-normal text-brand-dark mb-6">2. Le courrier de ma Caf</h2>

                <div className="mb-6">
                    <label className="block text-gray-700 font-bold text-sm mb-1">
                        Copie des courriers de votre Caf (PDF ou photos acceptés) <span className="text-brand-red">*</span>
                    </label>
                    <div
                        className={`border-2 border-dashed ${errors.file ? 'border-brand-red bg-red-50' : 'border-gray-400 bg-[#f0f4fa]'} p-10 text-center cursor-pointer transition-colors hover:bg-blue-50`}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            hidden
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            accept="image/*,application/pdf"
                            multiple
                        />
                        <div className="flex flex-col items-center justify-center text-gray-500">
                            {formData.files.length > 0 ? (
                                <div className="text-brand-dark font-medium w-full">
                                    <div className="mb-2 text-brand-red font-bold">{formData.files.length} fichier(s) sélectionné(s)</div>
                                    <ul className="text-left space-y-2">
                                        {formData.files.map((f, idx) => (
                                            <li key={idx} className="flex justify-between items-center bg-white p-2 rounded border border-gray-200 shadow-sm text-sm">
                                                <div className="flex items-center truncate">
                                                    <i className="fas fa-file-alt text-gray-400 mr-2"></i>
                                                    <span className="truncate max-w-[200px]">{f.name}</span>
                                                </div>
                                                <button
                                                    onClick={(e) => removeFile(idx, e)}
                                                    className="text-red-500 hover:text-red-700 ml-2 p-1"
                                                >
                                                    <i className="fas fa-times"></i>
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                    <p className="text-xs text-gray-400 mt-4">Cliquez ou glissez pour ajouter d'autres fichiers</p>
                                </div>
                            ) : (
                                <>
                                    <i className="fas fa-cloud-upload-alt text-4xl mb-3 text-gray-500"></i>
                                    <p className="text-sm">
                                        Glissez vos fichiers ici (ou) <span className="text-blue-500 underline">Parcourir</span>
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                    {errors.file && <p className="text-brand-red text-xs mt-1">{errors.file}</p>}
                </div>

                <div className="mb-2">
                    <label className="block text-gray-700 font-bold text-sm mb-1">
                        Description de votre affaire
                    </label>
                    <FormInput
                        label=""
                        name="description"
                        value={formData.description}
                        onChange={handleInputChange}
                        multiline
                    />
                    <p className="text-gray-500 text-xs mt-1 leading-relaxed">
                        Décrivez-moi brièvement pourquoi la Caf a tort et ce que j'ai besoin de savoir pour comprendre votre affaire. Ne vous en faites pas, je vous conseillerai également mes propres arguments.
                    </p>
                </div>
            </section>

            <section className="mb-8 space-y-4">
                <div className="flex items-start">
                    <div className="flex items-center h-5">
                        <input
                            id="type-confirm"
                            type="checkbox"
                            checked={agreedType}
                            onChange={(e) => setAgreedType(e.target.checked)}
                            className="w-5 h-5 border-2 border-gray-400 rounded-none focus:ring-brand-red text-brand-red"
                        />
                    </div>
                    <div className="ml-3 text-sm">
                        <label htmlFor="type-confirm" className="font-medium text-brand-dark">
                            Je confirme que ma demande concerne le RSA, la Prime d'activité, ou l'Aide au logement (APL, ALF, ALS). Le cabinet ne peut pas traiter les prestations liées au handicap, qui relèvent d'un tribunal différent.
                        </label>
                    </div>
                </div>

                <div className="flex items-start">
                    <div className="flex items-center h-5">
                        <input
                            id="privacy-confirm"
                            type="checkbox"
                            checked={agreedPrivacy}
                            onChange={(e) => setAgreedPrivacy(e.target.checked)}
                            className="w-5 h-5 border-2 border-gray-400 rounded-none focus:ring-brand-red text-brand-red"
                        />
                    </div>
                    <div className="ml-3 text-sm">
                        <label htmlFor="privacy-confirm" className="font-medium text-brand-dark">
                            Je consent à l'utilisation de mes données personnelles en accord avec la <span className="text-brand-red cursor-pointer">Politique de confidentialité</span> du cabinet.
                        </label>
                    </div>
                </div>
            </section>

            <section className="mb-8 space-y-4">
                <div className="flex items-center text-brand-dark text-lg">
                    <span className="bg-green-500 text-white rounded w-6 h-6 flex items-center justify-center mr-3 text-xs">
                        <i className="fas fa-check"></i>
                    </span>
                    Garantie sans engagement
                </div>
                <div className="flex items-center text-brand-dark text-lg">
                    <span className="bg-green-500 text-white rounded w-6 h-6 flex items-center justify-center mr-3 text-xs">
                        <i className="fas fa-check"></i>
                    </span>
                    Réponse sous 24 heures
                </div>
            </section>

            <button
                onClick={handleSubmit}
                disabled={isSubmitting || !agreedType || !agreedPrivacy}
                className={`w-full md:w-auto bg-brand-red hover:bg-[#b01938] text-white font-bold py-4 px-8 uppercase tracking-wider text-sm transition-colors ${isSubmitting || !agreedType || !agreedPrivacy ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {isSubmitting ? (
                    <span><i className="fas fa-circle-notch fa-spin mr-2"></i> Traitement...</span>
                ) : "Connaître mes chances de succès"}
            </button>

        </div>
    );
};