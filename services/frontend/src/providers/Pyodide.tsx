"use client";

import { createContext, useContext, ReactNode } from "react";
import { usePyodide } from "@/hooks/use-pyodide";

type PyodideContextType = ReturnType<typeof usePyodide>;

const PyodideContext = createContext<PyodideContextType | null>(null);

export function PyodideProvider({ children }: { children: ReactNode }) {
    const pyodide = usePyodide();

    return (
        <PyodideContext.Provider value={pyodide}>
            {children}
        </PyodideContext.Provider>
    );
}

export function usePyodideContext() {
    const context = useContext(PyodideContext);
    if (!context) {
        throw new Error("usePyodideContext must be used within PyodideProvider");
    }
    return context;
}