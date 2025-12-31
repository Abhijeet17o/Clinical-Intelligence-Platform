import React from "react";

type IconProps = {
    className?: string;
    size?: number;
    title?: string;
};

export const HomeIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Home" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 11.5L12 4l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1V11.5z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const PlusIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Add" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const PharmacyIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Pharmacy" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M4 12c0-2.5 2-4.5 4.5-4.5S13 9.5 13 12c0 2.5-2 4.5-4.5 4.5S4 14.5 4 12zM14.5 9.5 19 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const RobotIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "AI" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <rect x="3" y="6" width="18" height="12" rx="3" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M9 12h.01M15 12h.01M12 6v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const WarningIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Warning" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h15.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 9v4M12 17h.01" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const PrintIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Print" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M6 9V3h12v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M6 14h12v7H6z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const HeartIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Vital" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const NoteIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Notes" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M7 7h10M7 11h10M7 15h7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.2" />
    </svg>
);

export const LabIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Lab" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M8 21h8M7 3h10" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 3v7a3 3 0 0 0 3 3h0a3 3 0 0 0 3-3V3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const VaccineIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Vaccine" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M21 3l-6 6M3 21l6-6M14 7l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        <rect x="7" y="13" width="10" height="4" rx="1" stroke="currentColor" strokeWidth="1.2"/>
    </svg>
);

export const ClipboardIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Clipboard" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M9 2h6a2 2 0 0 1 2 2v1H7V4a2 2 0 0 1 2-2z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
        <rect x="3" y="6" width="18" height="15" rx="2" stroke="currentColor" strokeWidth="1.3" />
    </svg>
);

export const SearchIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Search" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="1.5" />
    </svg>
);

export const CalendarIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Calendar" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.4" />
        <path d="M16 3v4M8 3v4M3 11h18" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const RefreshIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Refresh" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M20 12a8 8 0 1 0-2.1 5.2L20 21" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const ChartIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Chart" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 3v18h18" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 13v-6M12 17v-10M17 9v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const BookIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Book" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M4 19.5A2 2 0 0 1 6 18h12" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M4 5.5A2 2 0 0 1 6 4h12v15" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const SaveIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Save" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M19 21H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3l2-2h4l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const TrashIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Delete" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 6h18" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 6v12M16 6v12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M10 6V4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const QuestionIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Help" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M12 17h.01M9.09 9a3 3 0 1 1 5.82 1c0 1-1 1.5-1.5 1.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.2" />
    </svg>
);

export const MailIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Email" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 8v8a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M21 8l-9 6L3 8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const LockIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Lock" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="1.2" />
        <path d="M7 11V8a5 5 0 0 1 10 0v3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const EyeIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Show" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.3" />
    </svg>
);

export const EyeOffIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Hide" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M10.58 10.58a3 3 0 0 0 4.24 4.24" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M2 12s4-7 10-7a11 11 0 0 1 4 1.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const UsersIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Users" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.3" />
        <path d="M20 8v1" stroke="currentColor" strokeWidth="1.3" />
    </svg>
);

export const PhoneIcon: React.FC<IconProps> = ({ className = "", size = 16, title = "Phone" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M22 16.92V20a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2 4.18 2 2 0 0 1 4 2h3.09a1 1 0 0 1 1 .75 12.64 12.64 0 0 0 .7 2.81 1 1 0 0 1-.24 1L7.91 8.91a16 16 0 0 0 6 6l1.35-1.35a1 1 0 0 1 1-.24 12.64 12.64 0 0 0 2.81.7 1 1 0 0 1 .75 1V20z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
);

export const MicrophoneIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Microphone" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M12 1v11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="7" y="4" width="10" height="7" rx="5" stroke="currentColor" strokeWidth="1.2" />
        <path d="M19 11v2a6 6 0 0 1-12 0v-2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const StopIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Stop" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <rect x="6" y="6" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.4" />
    </svg>
);

export const RecordDotIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Record" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <circle cx="12" cy="12" r="5" fill="currentColor" />
    </svg>
);

export const PackageIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Package" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M21 16V8a2 2 0 0 0-1-1.73L13 3l-7 3.27A2 2 0 0 0 5 8v8a2 2 0 0 0 1 1.73L11 21l7-3.27A2 2 0 0 0 21 16z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 7l9 4 9-4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export const LineChartIcon: React.FC<IconProps> = ({ className = "", size = 20, title = "Line Chart" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M3 3v18h18" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <polyline points="6 14 10 10 14 12 18 8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
);

export const EraserIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Eraser" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M20.5 10.5L13.5 3.5a2 2 0 0 0-2.83 0L3.5 10.5a2 2 0 0 0 0 2.83l6 6a2 2 0 0 0 2.83 0l7-7a2 2 0 0 0 0-2.83z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 17l3-3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

// Hospital building icon
export const HospitalIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Hospital" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <rect x="3" y="7" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.2" />
        <path d="M8 3v4M16 3v4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 10v6M9 13h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

// Medicine / capsule icon
export const MedicineIcon: React.FC<IconProps> = ({ className = "", size = 18, title = "Medicine" }) => (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label={title} role="img">
        <path d="M21 7c1.1 1.1 1.1 2.9 0 4L13 19c-1.1 1.1-2.9 1.1-4 0L3 13c-1.1-1.1-1.1-2.9 0-4L11 3c1.1-1.1 2.9-1.1 4 0l6 4z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 16l8-8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

export default {};
