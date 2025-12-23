import React from 'react';

interface FormInputProps {
    label: string;
    required?: boolean;
    type?: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    error?: string;
    multiline?: boolean;
    name: string;
    placeholder?: string;
}

export const FormInput: React.FC<FormInputProps> = ({ 
    label, required, type = "text", value, onChange, error, multiline, name, placeholder 
}) => {
    const baseClasses = "w-full bg-[#f0f4fa] border border-gray-400 p-3 mt-1 focus:outline-none focus:border-brand-red focus:ring-1 focus:ring-brand-red transition-colors";
    
    return (
        <div className="mb-6">
            <label className="block text-gray-700 font-bold text-sm mb-1">
                {label} {required && <span className="text-brand-red">*</span>}
            </label>
            {multiline ? (
                <textarea 
                    name={name}
                    rows={6}
                    className={`${baseClasses} resize-y min-h-[120px]`}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                />
            ) : (
                <input 
                    type={type} 
                    name={name}
                    className={`${baseClasses} h-10`}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                />
            )}
            {error && <p className="text-brand-red text-xs mt-1">{error}</p>}
        </div>
    );
};