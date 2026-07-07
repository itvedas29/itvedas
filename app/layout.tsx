import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { generateWebsiteSchema, generateOrganizationSchema } from '@/lib/seo/schema';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://itvedas.com';
const SITE_NAME = 'ITVedas';
const SITE_DESCRIPTION =
  'The largest vendor-neutral IT Knowledge Base. Learn IT topics from networking and cloud to security and Linux administration.';

export const metadata: Metadata = {
  title: {
    default: 'ITVedas - Professional IT Knowledge Base',
    template: '%s | ITVedas',
  },
  description: SITE_DESCRIPTION,
  keywords: [
    'IT knowledge base',
    'networking',
    'cloud computing',
    'cybersecurity',
    'Linux',
    'Windows',
    'IT administration',
    'DevOps',
  ],
  metadataBase: new URL(SITE_URL),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: SITE_URL,
    siteName: SITE_NAME,
    title: 'ITVedas - Professional IT Knowledge Base',
    description: SITE_DESCRIPTION,
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: SITE_NAME,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ITVedas - Professional IT Knowledge Base',
    description: SITE_DESCRIPTION,
    images: ['/twitter-image.png'],
    creator: '@itvedas',
  },
  robots: {
    index: true,
    follow: true,
    'max-image-preview': 'large',
    'max-snippet': -1,
    'max-video-preview': -1,
  },
  alternates: {
    canonical: SITE_URL,
    types: {
      'application/rss+xml': '/rss.xml',
    },
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  colorScheme: 'light dark',
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  const websiteSchema = generateWebsiteSchema();
  const organizationSchema = generateOrganizationSchema();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />
      </head>
      <body className={inter.variable}>
        <div className="min-h-screen bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-50">
          {children}
        </div>
      </body>
    </html>
  );
}
