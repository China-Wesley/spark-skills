#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

function usage() {
  console.error('Usage: node browser_smoke.mjs <prototype-output-directory>');
}

const input = process.argv[2];
if (!input) {
  usage();
  process.exit(2);
}

let playwright;
try {
  playwright = await import('playwright');
} catch (error) {
  console.error('Playwright is not available in this Node environment.');
  console.error('Install Playwright in an isolated or project-approved environment, or run the journey manually in a browser.');
  process.exit(2);
}

const root = path.resolve(input);
const specPath = path.join(root, 'prototype-spec.json');
const prototypePath = path.join(root, 'prototype.html');
const shellPath = path.join(root, 'index.html');
const screenshotDir = path.join(root, 'screenshots');
const spec = JSON.parse(await fs.readFile(specPath, 'utf8'));
await fs.mkdir(screenshotDir, { recursive: true });

const failures = [];
const pageErrors = [];
const consoleErrors = [];
const completedSteps = [];
const viewport = spec.primary_viewport || { width: 390, height: 844 };
const browser = await playwright.chromium.launch({ headless: true });

async function assertExpectation(page, expectation, label) {
  if (!expectation) return;
  if (expectation.screen) {
    await page.locator(`[data-screen="${expectation.screen}"]`).waitFor({ state: 'visible', timeout: 5000 });
  }
  if (expectation.visible) {
    await page.locator(expectation.visible).waitFor({ state: 'visible', timeout: 5000 });
  }
  if (expectation.text) {
    const actual = await page.locator(expectation.text.selector).innerText({ timeout: 5000 });
    if (!actual.includes(expectation.text.includes)) {
      throw new Error(`${label}: expected ${expectation.text.selector} to include ${JSON.stringify(expectation.text.includes)}, got ${JSON.stringify(actual)}`);
    }
  }
}

try {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });

  await page.goto(pathToFileURL(prototypePath).href, { waitUntil: 'load' });
  await page.screenshot({ path: path.join(screenshotDir, 'step-00-start.png'), fullPage: true });

  const steps = spec.primary_journey?.steps || [];
  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    const label = `step ${index + 1} (${step.action})`;
    try {
      if (step.action === 'click') await page.locator(step.selector).click();
      else if (step.action === 'fill') await page.locator(step.selector).fill(String(step.value));
      else if (step.action === 'select') await page.locator(step.selector).selectOption(String(step.value));
      else if (step.action === 'press') await page.locator(step.selector).press(String(step.value));
      else if (step.action === 'wait') await page.waitForTimeout(Math.min(5000, Math.max(0, Number(step.value))));
      else throw new Error(`Unsupported action: ${step.action}`);

      await assertExpectation(page, step.expect, label);
      await page.screenshot({
        path: path.join(screenshotDir, `step-${String(index + 1).padStart(2, '0')}-${step.action}.png`),
        fullPage: true,
      });
      completedSteps.push({ index: index + 1, action: step.action, selector: step.selector || null, ok: true });
    } catch (error) {
      failures.push(`${label}: ${error instanceof Error ? error.message : String(error)}`);
      completedSteps.push({ index: index + 1, action: step.action, selector: step.selector || null, ok: false });
      break;
    }
  }
  await context.close();

  const overviewContext = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const overview = await overviewContext.newPage();
  overview.on('pageerror', error => pageErrors.push(`overview: ${String(error)}`));
  overview.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(`overview: ${message.text()}`);
  });
  await overview.goto(pathToFileURL(shellPath).href, { waitUntil: 'load' });
  await overview.waitForTimeout(300);
  await overview.screenshot({ path: path.join(screenshotDir, 'overview.png'), fullPage: true });
  await overviewContext.close();
} finally {
  await browser.close();
}

if (pageErrors.length) failures.push(...pageErrors.map(error => `pageerror: ${error}`));
if (consoleErrors.length) failures.push(...consoleErrors.map(error => `console error: ${error}`));

const report = {
  ok: failures.length === 0,
  root,
  journey: spec.primary_journey?.id || null,
  completed_steps: completedSteps,
  page_errors: pageErrors,
  console_errors: consoleErrors,
  failures,
};

await fs.writeFile(path.join(screenshotDir, 'browser-smoke.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(report, null, 2));
process.exit(report.ok ? 0 : 1);
