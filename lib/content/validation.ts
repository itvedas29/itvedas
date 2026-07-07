import { ArticleFrontmatter } from '@types/article';

export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

export function validateArticle(
  frontmatter: Partial<ArticleFrontmatter>,
  content: string
): ValidationError[] {
  const errors: ValidationError[] = [];

  // Required fields
  if (!frontmatter.title) {
    errors.push({ field: 'title', message: 'Title is required', severity: 'error' });
  } else if (frontmatter.title.length < 10) {
    errors.push({
      field: 'title',
      message: 'Title should be at least 10 characters',
      severity: 'warning',
    });
  } else if (frontmatter.title.length > 100) {
    errors.push({
      field: 'title',
      message: 'Title should not exceed 100 characters',
      severity: 'warning',
    });
  }

  if (!frontmatter.description) {
    errors.push({ field: 'description', message: 'Description is required', severity: 'error' });
  } else if (frontmatter.description.length < 50) {
    errors.push({
      field: 'description',
      message: 'Description should be at least 50 characters',
      severity: 'warning',
    });
  } else if (frontmatter.description.length > 160) {
    errors.push({
      field: 'description',
      message: 'Description should not exceed 160 characters',
      severity: 'warning',
    });
  }

  if (!frontmatter.slug) {
    errors.push({ field: 'slug', message: 'Slug is required', severity: 'error' });
  } else if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(frontmatter.slug)) {
    errors.push({
      field: 'slug',
      message: 'Slug should contain only lowercase letters, numbers, and hyphens',
      severity: 'error',
    });
  }

  if (!frontmatter.category) {
    errors.push({ field: 'category', message: 'Category is required', severity: 'error' });
  }

  if (!frontmatter.tags || frontmatter.tags.length === 0) {
    errors.push({
      field: 'tags',
      message: 'At least one tag is required',
      severity: 'warning',
    });
  } else if (frontmatter.tags.length > 10) {
    errors.push({
      field: 'tags',
      message: 'Should not have more than 10 tags',
      severity: 'warning',
    });
  }

  if (!frontmatter.keywords || frontmatter.keywords.length === 0) {
    errors.push({
      field: 'keywords',
      message: 'At least one keyword is required',
      severity: 'warning',
    });
  } else if (frontmatter.keywords.length > 20) {
    errors.push({
      field: 'keywords',
      message: 'Should not have more than 20 keywords',
      severity: 'warning',
    });
  }

  if (!frontmatter.published) {
    errors.push({
      field: 'published',
      message: 'Published date is required',
      severity: 'error',
    });
  }

  if (!frontmatter.lastUpdated) {
    errors.push({
      field: 'lastUpdated',
      message: 'Last updated date is required',
      severity: 'error',
    });
  }

  // Content validation
  const wordCount = content.split(/\s+/).length;
  if (wordCount < 2500) {
    errors.push({
      field: 'content',
      message: `Article is too short (${wordCount} words). Target: 2500-4500 words.`,
      severity: 'warning',
    });
  } else if (wordCount > 4500) {
    errors.push({
      field: 'content',
      message: `Article is too long (${wordCount} words). Target: 2500-4500 words.`,
      severity: 'warning',
    });
  }

  // Check for required sections
  const requiredSections = [
    'Introduction',
    'What is',
    'Why is',
    'Core Concepts',
    'Advantages',
    'Limitations',
    'Best Practices',
    'Common Mistakes',
    'FAQ',
    'Glossary',
    'Summary',
  ];

  const contentLower = content.toLowerCase();
  const missingSections = requiredSections.filter((section) => !contentLower.includes(section.toLowerCase()));

  if (missingSections.length > 0) {
    errors.push({
      field: 'content',
      message: `Missing recommended sections: ${missingSections.join(', ')}`,
      severity: 'warning',
    });
  }

  // Check for minimum internal links
  const internalLinkCount = (content.match(/\[.*?\]\(\/knowledge\//g) || []).length;
  if (internalLinkCount < 10) {
    errors.push({
      field: 'content',
      message: `Article should have at least 10 internal links. Found: ${internalLinkCount}`,
      severity: 'warning',
    });
  }

  return errors;
}

export function hasErrors(errors: ValidationError[]): boolean {
  return errors.some((e) => e.severity === 'error');
}

export function hasWarnings(errors: ValidationError[]): boolean {
  return errors.some((e) => e.severity === 'warning');
}

export function formatValidationErrors(errors: ValidationError[]): string {
  const errorLines = errors.map(
    (e) => `[${e.severity.toUpperCase()}] ${e.field}: ${e.message}`
  );
  return errorLines.join('\n');
}
