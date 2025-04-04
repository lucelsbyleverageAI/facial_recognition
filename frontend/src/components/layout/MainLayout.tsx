'use client';

import { ReactNode } from 'react';
import { Header } from './Header';
import { Toaster } from '@/components/ui/toaster';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-background via-background to-muted/30">
      <Header />
      <main className="flex-1 py-8 px-4 md:py-12 md:px-6">
        <div className="container mx-auto max-w-7xl">
          {children}
        </div>
      </main>
      <footer className="py-6 border-t bg-muted/10">
        <div className="container mx-auto max-w-7xl text-center text-sm text-muted-foreground">
          <p>Facial Recognition Processing System</p>
        </div>
      </footer>
      <Toaster />
    </div>
  );
} 