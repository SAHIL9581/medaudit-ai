import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Send, Bot, User, Loader2, ChevronDown } from "lucide-react";
import { sendChatMessage } from "../services/api";

/* ── Language-specific UI strings ─────────────────────────────────────── */
const UI_TEXT = {
    en: {
        title: "Your Bill Helper 🤖",
        subtitle: "Ask me anything!",
        welcome:
            "Hi there! 👋 I'm here to help you understand your hospital bill in simple words.\n\nTry asking me:\n- Why was I charged so much?\n- Was I billed for something twice?\n- What should I do to get my money back?",
        placeholder: "Type your question here...",
        footer: "I only know about your uploaded bill",
        thinking: "Looking into this for you...",
        chips: [
            "🚨 Why was I flagged?",
            "🔄 Was I charged twice?",
            "📋 What should I do next?",
            "💰 Why is this price so high?",
        ],
        close: "Close",
        open: "Ask a Question 💬",
    },
    hi: {
        title: "आपका बिल सहायक 🤖",
        subtitle: "कुछ भी पूछें!",
        welcome:
            "नमस्ते! 👋 मैं आपके अस्पताल के बिल को आसान भाषा में समझाने के लिए यहाँ हूं।\n\nपूछें:\n- मुझे इतना ज़्यादा क्यों चार्ज किया गया?\n- क्या कोई चीज़ दो बार बिल हुई?\n- पैसे वापस पाने के लिए मुझे क्या करना चाहिए?",
        placeholder: "यहाँ अपना सवाल लिखें...",
        footer: "मैं केवल आपके बिल के बारे में जानता हूं",
        thinking: "देख रहा हूं...",
        chips: [
            "🚨 मुझे क्यों फ्लैग किया गया?",
            "🔄 क्या दो बार चार्ज हुआ?",
            "📋 मुझे आगे क्या करना चाहिए?",
            "💰 यह कीमत इतनी ज़्यादा क्यों है?",
        ],
        close: "बंद करें",
        open: "सवाल पूछें 💬",
    },
    ta: {
        title: "உங்கள் பில் உதவியாளர் 🤖",
        subtitle: "எதையும் கேளுங்கள்!",
        welcome:
            "வணக்கம்! 👋 உங்கள் மருத்துவமனை பில்லை எளிய வார்த்தைகளில் புரிய வைக்க நான் இங்கே இருக்கிறேன்.\n\nகேளுங்கள்:\n- ஏன் இவ்வளவு கட்டணம் வசூலிக்கப்பட்டது?\n- ஏதாவது இரண்டு முறை கட்டணம் வசூலிக்கப்பட்டதா?\n- பணம் திரும்பப் பெற நான் என்ன செய்ய வேண்டும்?",
        placeholder: "உங்கள் கேள்வியை இங்கே தட்டச்சு செய்யுங்கள்...",
        footer: "உங்கள் பில் பற்றி மட்டுமே தெரியும்",
        thinking: "பார்க்கிறேன்...",
        chips: [
            "🚨 ஏன் கொடியிடப்பட்டது?",
            "🔄 இரண்டு முறை வசூலிக்கப்பட்டதா?",
            "📋 அடுத்து என்ன செய்வது?",
            "💰 விலை ஏன் இவ்வளவு அதிகம்?",
        ],
        close: "மூடு",
        open: "கேள்வி கேளுங்கள் 💬",
    },
    es: {
        title: "Tu Asistente de Factura 🤖",
        subtitle: "¡Pregunta lo que quieras!",
        welcome:
            "¡Hola! 👋 Estoy aquí para ayudarte a entender tu factura del hospital en palabras simples.\n\nPuedes preguntar:\n- ¿Por qué me cobraron tanto?\n- ¿Me cobraron algo dos veces?\n- ¿Qué debo hacer para recuperar mi dinero?",
        placeholder: "Escribe tu pregunta aquí...",
        footer: "Solo sé sobre tu factura subida",
        thinking: "Buscando respuesta...",
        chips: [
            "🚨 ¿Por qué me marcaron?",
            "🔄 ¿Me cobraron dos veces?",
            "📋 ¿Qué debo hacer ahora?",
            "💰 ¿Por qué el precio es tan alto?",
        ],
        close: "Cerrar",
        open: "Hacer una Pregunta 💬",
    },
};

/* ── Simple inline-bold renderer ──────────────────────────────────────── */
function renderBold(text) {
    const parts = text.split(/\*\*(.+?)\*\*/g);
    return parts.map((p, i) =>
        i % 2 === 1 ? (
            <strong key={i} className="font-semibold text-white">
                {p}
            </strong>
        ) : (
            p
        )
    );
}

/* ── Parse AI text into structured items ──────────────────────────────── */
function parseResponse(text) {
    const lines = text.split("\n");
    const items = [];
    for (const line of lines) {
        const t = line.trim();
        if (!t) {
            items.push({ type: "spacer" });
            continue;
        }
        const numMatch = t.match(/^(\d+)[.)]\s+(.+)/);
        if (numMatch) { items.push({ type: "numbered", num: numMatch[1], text: numMatch[2] }); continue; }
        if (t.startsWith("- ") || t.startsWith("• ")) {
            items.push({ type: "bullet", text: t.replace(/^[-•]\s+/, "") }); continue;
        }
        if ((t.endsWith(":") && t.length < 80) || /^\*\*(.+)\*\*$/.test(t)) {
            items.push({ type: "heading", text: t.replace(/\*\*/g, "") }); continue;
        }
        items.push({ type: "paragraph", text: t });
    }
    // Collapse multiple spacers
    return items.filter((x, i) => !(x.type === "spacer" && items[i - 1]?.type === "spacer"));
}

/* ── Structured bot message renderer ─────────────────────────────────── */
const StructuredContent = ({ text }) => {
    const items = parseResponse(text);
    return (
        <div className="space-y-1.5 text-sm">
            {items.map((item, i) => {
                if (item.type === "spacer") return <div key={i} className="h-1" />;
                if (item.type === "heading")
                    return (
                        <p key={i} className="text-[11px] font-bold uppercase tracking-wider text-blue-300 pt-1">
                            {item.text}
                        </p>
                    );
                if (item.type === "numbered")
                    return (
                        <div key={i} className="flex items-start gap-2">
                            <span className="shrink-0 w-5 h-5 rounded-full bg-blue-500/25 text-blue-300 text-[10px] font-bold flex items-center justify-center mt-0.5">
                                {item.num}
                            </span>
                            <p className="leading-relaxed">{renderBold(item.text)}</p>
                        </div>
                    );
                if (item.type === "bullet")
                    return (
                        <div key={i} className="flex items-start gap-2">
                            <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-blue-400 mt-2" />
                            <p className="leading-relaxed">{renderBold(item.text)}</p>
                        </div>
                    );
                return <p key={i} className="leading-relaxed">{renderBold(item.text)}</p>;
            })}
        </div>
    );
};

/* ── Single message bubble ─────────────────────────────────────────────── */
const Message = ({ msg }) => {
    const isBot = msg.role === "assistant";
    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-start gap-2.5 ${isBot ? "" : "flex-row-reverse"}`}
        >
            <div
                className={`shrink-0 p-1.5 rounded-lg border ${
                    isBot ? "bg-blue-500/15 border-blue-500/20" : "bg-slate-700/50 border-slate-600/30"
                }`}
            >
                {isBot ? (
                    <Bot className="w-3.5 h-3.5 text-blue-400" />
                ) : (
                    <User className="w-3.5 h-3.5 text-slate-400" />
                )}
            </div>
            <div
                className={`max-w-[82%] rounded-xl px-3.5 py-2.5 ${
                    isBot
                        ? "bg-[#0d1f3c] border border-[#1e3a5f]/60 text-slate-200"
                        : "bg-blue-600/20 border border-blue-500/25 text-slate-100 text-sm leading-relaxed"
                }`}
            >
                {isBot ? <StructuredContent text={msg.content} /> : msg.content}
            </div>
        </motion.div>
    );
};

/* ── Main Chatbot component (only rendered when auditResult exists) ─────── */
export default function Chatbot({ auditResult, language }) {
    const t = UI_TEXT[language] || UI_TEXT.en;
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([{ role: "assistant", content: t.welcome }]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef(null);

    // Reset chat with translated welcome when language changes
    useEffect(() => {
        setMessages([{ role: "assistant", content: t.welcome }]);
    }, [language]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, open]);

    const handleSend = async (question = input) => {
        const trimmed = question.trim();
        if (!trimmed || loading) return;
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
        setLoading(true);
        try {
            const answer = await sendChatMessage(trimmed, auditResult || {}, language || "en");
            setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
        } catch (e) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "⚠️ Sorry, something went wrong. Please try asking again." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
    };

    const isFirstMessage = messages.length === 1;

    return (
        <>
            {/* Floating button */}
            <button
                onClick={() => setOpen((v) => !v)}
                className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3
                           bg-blue-600 hover:bg-blue-500 active:bg-blue-700
                           text-white font-semibold text-sm rounded-2xl shadow-2xl
                           border border-blue-400/30 transition-all duration-200"
                aria-label="Toggle AI Chat"
            >
                <MessageCircle className="w-4 h-4" />
                <span className="hidden sm:inline">{open ? t.close : t.open}</span>
            </button>

            {/* Chat panel */}
            <AnimatePresence>
                {open && (
                    <motion.div
                        key="chat-panel"
                        initial={{ opacity: 0, y: 24, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 24, scale: 0.97 }}
                        transition={{ duration: 0.2 }}
                        className="fixed bottom-20 right-6 z-50 w-[360px] sm:w-[420px]
                                   flex flex-col rounded-2xl border border-[#1e3a5f]/60
                                   bg-[#060d1a]/97 backdrop-blur-xl shadow-2xl overflow-hidden"
                        style={{ maxHeight: "540px" }}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-4 py-3
                                        border-b border-[#1e3a5f]/50 bg-[#0a1628]/90 shrink-0">
                            <div className="flex items-center gap-2.5">
                                <div className="p-1.5 bg-blue-500/15 rounded-lg border border-blue-500/20">
                                    <Bot className="w-4 h-4 text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-white">{t.title}</p>
                                    <p className="text-[10px] text-emerald-400 font-medium">{t.subtitle}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setOpen(false)}
                                className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500
                                           hover:text-slate-300 transition-colors text-xs font-medium"
                            >
                                <ChevronDown className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
                            {messages.map((msg, i) => (
                                <Message key={i} msg={msg} />
                            ))}
                            {loading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex items-center gap-2 text-slate-400 text-xs pl-1"
                                >
                                    <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
                                    {t.thinking}
                                </motion.div>
                            )}
                            <div ref={bottomRef} />
                        </div>

                        {/* Suggestion chips — only before first user message */}
                        {isFirstMessage && (
                            <div className="px-4 pb-3 flex flex-wrap gap-1.5 shrink-0">
                                {t.chips.map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => handleSend(q)}
                                        className="text-[11px] px-2.5 py-1.5 rounded-full border border-blue-500/30
                                                   bg-blue-500/8 text-blue-300 hover:bg-blue-500/20 transition-colors
                                                   font-medium"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Input row */}
                        <div className="px-3 pb-3 pt-1 border-t border-[#1e3a5f]/50 bg-[#060d1a]/80 shrink-0">
                            <div className="flex items-end gap-2 rounded-xl border border-[#1e3a5f]/60
                                            bg-[#0a1628]/80 px-3 py-2">
                                <textarea
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder={t.placeholder}
                                    rows={1}
                                    className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600
                                               resize-none outline-none max-h-28 leading-relaxed"
                                />
                                <button
                                    onClick={() => handleSend()}
                                    disabled={!input.trim() || loading}
                                    className="shrink-0 p-2 rounded-lg bg-blue-600 hover:bg-blue-500
                                               disabled:opacity-40 disabled:cursor-not-allowed
                                               text-white transition-colors"
                                    aria-label="Send"
                                >
                                    <Send className="w-3.5 h-3.5" />
                                </button>
                            </div>
                            <p className="text-[10px] text-slate-600 mt-1.5 text-center">{t.footer}</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}