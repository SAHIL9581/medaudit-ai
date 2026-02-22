import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
        baseURL: BASE_URL,
        timeout: 180000, // 3 minutes for large PDFs + GPT
});

api.interceptors.response.use(
        (res) => res,
        (err) => {
                const message =
                        err.response?.data?.detail ||
                        err.response?.data?.message ||
                        err.message ||
                        "An unexpected error occurred.";
                return Promise.reject(new Error(message));
        }
);

export const auditBill = async (files, onUploadProgress) => {
        const formData = new FormData();
        formData.append("bill_pdf", files.bill);
        if (files.summary) formData.append("summary_pdf", files.summary);
        if (files.eob) formData.append("eob_pdf", files.eob);

        const { data } = await api.post("/api/audit/analyze", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                onUploadProgress,
        });
        return data;
};

export const downloadAppealPDF = async (appealData) => {
        const response = await api.post("/api/audit/download-letter", appealData, {
                responseType: "blob",
        });
        const url = window.URL.createObjectURL(
                new Blob([response.data], { type: "application/pdf" })
        );
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "appeal_letter.pdf");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
};

export const healthCheck = () => api.get("/api/audit/health");

export default api;
