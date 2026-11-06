import { defineConfig } from '@playwright/test';
import baseline from './playwright.config';

export default defineConfig({ ...baseline, testDir: './tests/acceptance', timeout: 15_000 });
