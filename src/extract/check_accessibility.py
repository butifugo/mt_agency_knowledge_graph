#!/bin/sh
''''exec "$(dirname "$0")/../.venv/bin/python" "$0" "$@" # '''
"""
WCAG 2.0 Level AA Accessibility Checker
Fetches live web pages and checks for common accessibility issues
"""

import re
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
import sys
from urllib.parse import urljoin, urlparse
import time

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class WCAGChecker:
    def __init__(self, url):
        self.url = url
        self.html_content = self.fetch_page(url)
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def fetch_page(self, url):
        """Fetch HTML content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}")
    
    def check_all(self):
        """Run all WCAG AA checks"""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"WCAG 2.0 Level AA Accessibility Check")
        print(f"URL: {self.url}")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        # Text Alternatives (1.1.1)
        self.check_image_alt_text()
        
        # Color Contrast (1.4.3)
        self.check_color_contrast()
        
        # Keyboard Accessible (2.1.1, 2.1.2)
        self.check_keyboard_accessibility()
        
        # Focus Visible (2.4.7)
        self.check_focus_indicators()
        
        # Page Titled (2.4.2)
        self.check_page_title()
        
        # Headings and Labels (2.4.6)
        self.check_headings()
        
        # Link Purpose (2.4.4)
        self.check_link_text()
        
        # Language of Page (3.1.1)
        self.check_language()
        
        # Labels or Instructions (3.3.2)
        self.check_form_labels()
        
        # Name, Role, Value (4.1.2)
        self.check_aria_attributes()
        
        # Parsing (4.1.1)
        self.check_html_validity()
        
        # Additional checks
        self.check_semantic_html()
        self.check_skip_links()
        
        self.print_results()
    
    def check_image_alt_text(self):
        """1.1.1 - Non-text Content"""
        images = self.soup.find_all('img')
        images_without_alt = []
        
        for img in images:
            if not img.get('alt'):
                images_without_alt.append(str(img)[:100])
        
        if images_without_alt:
            self.issues.append({
                'guideline': '1.1.1 - Non-text Content',
                'level': 'A',
                'message': f'Found {len(images_without_alt)} image(s) without alt text',
                'details': images_without_alt[:5]  # Show first 5
            })
        else:
            self.passed.append('1.1.1 - All images have alt text')
    
    def check_color_contrast(self):
        """1.4.3 - Contrast (Minimum)"""
        # Check for inline styles with color - needs manual review
        elements_with_color = self.soup.find_all(style=re.compile(r'color\s*:'))
        
        if elements_with_color:
            self.warnings.append({
                'guideline': '1.4.3 - Contrast (Minimum)',
                'level': 'AA',
                'message': f'Found {len(elements_with_color)} element(s) with inline color styles - manual contrast check needed',
                'details': 'Ensure contrast ratio is at least 4.5:1 for normal text, 3:1 for large text'
            })
        else:
            self.warnings.append({
                'guideline': '1.4.3 - Contrast (Minimum)',
                'level': 'AA',
                'message': 'Manual review needed for color contrast ratios',
                'details': 'Use browser dev tools or online tools to verify contrast'
            })
    
    def check_keyboard_accessibility(self):
        """2.1.1 - Keyboard, 2.1.2 - No Keyboard Trap"""
        # Check for elements that might need keyboard access
        interactive_elements = self.soup.find_all(['button', 'a', 'input', 'select', 'textarea'])
        
        # Check for onclick on non-interactive elements
        non_standard_interactive = self.soup.find_all(onclick=True)
        problematic = [elem for elem in non_standard_interactive 
                      if elem.name not in ['button', 'a', 'input', 'select', 'textarea']]
        
        if problematic:
            self.issues.append({
                'guideline': '2.1.1 - Keyboard',
                'level': 'A',
                'message': f'Found {len(problematic)} non-standard interactive element(s) that may not be keyboard accessible',
                'details': [elem.name for elem in problematic[:5]]
            })
        else:
            self.passed.append('2.1.1 - No obvious keyboard accessibility issues')
    
    def check_focus_indicators(self):
        """2.4.7 - Focus Visible"""
        style_tags = self.soup.find_all('style')
        removes_outline = False
        
        for style in style_tags:
            if style.string and re.search(r'outline\s*:\s*(?:none|0)', style.string):
                removes_outline = True
                break
        
        if removes_outline:
            self.warnings.append({
                'guideline': '2.4.7 - Focus Visible',
                'level': 'AA',
                'message': 'CSS removes focus outline - ensure custom focus indicators are provided',
                'details': 'Verify that focus is clearly visible on all interactive elements'
            })
        else:
            self.passed.append('2.4.7 - No focus outline removal detected')
    
    def check_page_title(self):
        """2.4.2 - Page Titled"""
        title = self.soup.find('title')
        
        if not title or not title.string or not title.string.strip():
            self.issues.append({
                'guideline': '2.4.2 - Page Titled',
                'level': 'A',
                'message': 'Page is missing a descriptive title',
                'details': 'Add a <title> element that describes the page topic or purpose'
            })
        else:
            self.passed.append(f'2.4.2 - Page has title: "{title.string.strip()}"')
    
    def check_headings(self):
        """2.4.6 - Headings and Labels"""
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            self.warnings.append({
                'guideline': '2.4.6 - Headings and Labels',
                'level': 'AA',
                'message': 'No heading elements found',
                'details': 'Consider using headings to organize content structure'
            })
        else:
            # Check heading hierarchy
            prev_level = 0
            hierarchy_issues = []
            
            for heading in headings:
                level = int(heading.name[1])
                if prev_level > 0 and level > prev_level + 1:
                    hierarchy_issues.append(f'Skipped from h{prev_level} to h{level}')
                prev_level = level
            
            if hierarchy_issues:
                self.warnings.append({
                    'guideline': '2.4.6 - Headings and Labels',
                    'level': 'AA',
                    'message': 'Heading hierarchy has gaps',
                    'details': hierarchy_issues[:5]
                })
            else:
                self.passed.append(f'2.4.6 - Found {len(headings)} headings with proper hierarchy')
    
    def check_link_text(self):
        """2.4.4 - Link Purpose (In Context)"""
        links = self.soup.find_all('a')
        vague_links = []
        
        vague_texts = ['click here', 'read more', 'more', 'link', 'here']
        
        for link in links:
            text = link.get_text().strip().lower()
            if text in vague_texts or not text:
                vague_links.append(link.get('href', 'no href')[:50])
        
        if vague_links:
            self.warnings.append({
                'guideline': '2.4.4 - Link Purpose',
                'level': 'A',
                'message': f'Found {len(vague_links)} link(s) with vague or missing text',
                'details': vague_links[:5]
            })
        else:
            self.passed.append('2.4.4 - All links have descriptive text')
    
    def check_language(self):
        """3.1.1 - Language of Page"""
        html_tag = self.soup.find('html')
        
        if not html_tag or not html_tag.get('lang'):
            self.issues.append({
                'guideline': '3.1.1 - Language of Page',
                'level': 'A',
                'message': 'Page language is not specified',
                'details': 'Add lang attribute to <html> tag (e.g., lang="en")'
            })
        else:
            self.passed.append(f'3.1.1 - Page language set to "{html_tag.get("lang")}"')
    
    def check_form_labels(self):
        """3.3.2 - Labels or Instructions"""
        inputs = self.soup.find_all(['input', 'select', 'textarea'])
        unlabeled = []
        
        for input_elem in inputs:
            input_type = input_elem.get('type', 'text')
            if input_type in ['hidden', 'submit', 'button']:
                continue
            
            input_id = input_elem.get('id')
            has_label = False
            
            # Check for associated label
            if input_id:
                label = self.soup.find('label', attrs={'for': input_id})
                if label:
                    has_label = True
            
            # Check for aria-label or aria-labelledby
            if input_elem.get('aria-label') or input_elem.get('aria-labelledby'):
                has_label = True
            
            # Check if wrapped in label
            parent = input_elem.parent
            if parent and parent.name == 'label':
                has_label = True
            
            if not has_label:
                unlabeled.append(str(input_elem)[:80])
        
        if unlabeled:
            self.issues.append({
                'guideline': '3.3.2 - Labels or Instructions',
                'level': 'A',
                'message': f'Found {len(unlabeled)} form input(s) without labels',
                'details': unlabeled[:5]
            })
        elif inputs:
            self.passed.append('3.3.2 - All form inputs have labels')
    
    def check_aria_attributes(self):
        """4.1.2 - Name, Role, Value"""
        elements_with_aria = self.soup.find_all(attrs={'role': True})
        
        issues = []
        for elem in elements_with_aria:
            role = elem.get('role')
            # Check if interactive roles have accessible names
            if role in ['button', 'link', 'checkbox', 'radio', 'menuitem']:
                has_name = (elem.get('aria-label') or 
                           elem.get('aria-labelledby') or 
                           elem.get_text().strip())
                if not has_name:
                    issues.append(f'{elem.name} with role="{role}" lacks accessible name')
        
        if issues:
            self.warnings.append({
                'guideline': '4.1.2 - Name, Role, Value',
                'level': 'A',
                'message': f'Found {len(issues)} ARIA element(s) potentially missing accessible names',
                'details': issues[:5]
            })
    
    def check_html_validity(self):
        """4.1.1 - Parsing"""
        # Check for duplicate IDs
        ids = {}
        duplicate_ids = []
        
        for elem in self.soup.find_all(id=True):
            elem_id = elem.get('id')
            if elem_id in ids:
                duplicate_ids.append(elem_id)
            ids[elem_id] = True
        
        if duplicate_ids:
            self.issues.append({
                'guideline': '4.1.1 - Parsing',
                'level': 'A',
                'message': f'Found {len(duplicate_ids)} duplicate ID(s)',
                'details': duplicate_ids[:5]
            })
        else:
            self.passed.append('4.1.1 - No duplicate IDs found')
    
    def check_semantic_html(self):
        """Best Practice - Semantic HTML"""
        semantic_elements = self.soup.find_all(['header', 'nav', 'main', 'article', 'section', 'aside', 'footer'])
        
        if not semantic_elements:
            self.warnings.append({
                'guideline': 'Best Practice - Semantic HTML',
                'level': 'Best Practice',
                'message': 'No HTML5 semantic elements found',
                'details': 'Consider using <header>, <nav>, <main>, <footer>, etc.'
            })
        else:
            self.passed.append(f'Best Practice - Found {len(semantic_elements)} semantic elements')
    
    def check_skip_links(self):
        """Best Practice - Skip Navigation"""
        first_link = self.soup.find('a')
        
        if first_link:
            href = first_link.get('href', '')
            text = first_link.get_text().strip().lower()
            
            if not (href.startswith('#') and 'skip' in text):
                self.warnings.append({
                    'guideline': 'Best Practice - Skip Navigation',
                    'level': 'Best Practice',
                    'message': 'Consider adding a "skip to main content" link',
                    'details': 'This helps keyboard users bypass repetitive navigation'
                })
    
    def print_results(self):
        """Print all results with color coding"""
        total_checks = len(self.issues) + len(self.warnings) + len(self.passed)
        
        # Print Issues (Errors)
        if self.issues:
            print(f"\n{Fore.RED}{'='*70}")
            print(f"❌ ISSUES FOUND ({len(self.issues)})")
            print(f"{'='*70}{Style.RESET_ALL}")
            
            for issue in self.issues:
                print(f"\n{Fore.RED}✗ {issue['guideline']} (Level {issue.get('level', 'N/A')}){Style.RESET_ALL}")
                print(f"  {issue['message']}")
                if 'details' in issue:
                    if isinstance(issue['details'], list):
                        for detail in issue['details']:
                            print(f"  - {detail}")
                    else:
                        print(f"  {issue['details']}")
        
        # Print Warnings
        if self.warnings:
            print(f"\n{Fore.YELLOW}{'='*70}")
            print(f"⚠️  WARNINGS ({len(self.warnings)})")
            print(f"{'='*70}{Style.RESET_ALL}")
            
            for warning in self.warnings:
                print(f"\n{Fore.YELLOW}⚠ {warning['guideline']} (Level {warning.get('level', 'N/A')}){Style.RESET_ALL}")
                print(f"  {warning['message']}")
                if 'details' in warning:
                    if isinstance(warning['details'], list):
                        for detail in warning['details']:
                            print(f"  - {detail}")
                    else:
                        print(f"  {warning['details']}")
        
        # Print Passed Checks
        if self.passed:
            print(f"\n{Fore.GREEN}{'='*70}")
            print(f"✓ PASSED CHECKS ({len(self.passed)})")
            print(f"{'='*70}{Style.RESET_ALL}")
            
            for check in self.passed:
                print(f"{Fore.GREEN}✓ {check}{Style.RESET_ALL}")
        
        # Summary
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.RED}Issues: {len(self.issues)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Warnings: {len(self.warnings)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Passed: {len(self.passed)}{Style.RESET_ALL}")
        
        if self.issues:
            print(f"\n{Fore.RED}⚠️  Critical accessibility issues found - please address before publishing{Style.RESET_ALL}")
        elif self.warnings:
            print(f"\n{Fore.YELLOW}✓ No critical issues, but some warnings need review{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✓ All automated checks passed!{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Note: This is an automated check. Manual testing with screen readers")
        print(f"and keyboard navigation is still required for full WCAG compliance.{Style.RESET_ALL}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_accessibility.py <url> [url2] [url3] ...")
        print("Example: python check_accessibility.py https://example.com")
        print("         python check_accessibility.py https://site1.com https://site2.com")
        sys.exit(1)
    
    urls = sys.argv[1:]
    
    all_results = []
    
    for i, url in enumerate(urls):
        try:
            if i > 0:
                print(f"\n\n{Fore.CYAN}{'='*70}")
                print(f"Waiting 2 seconds before next request...")
                print(f"{'='*70}{Style.RESET_ALL}")
                time.sleep(2)  # Be polite to servers
            
            checker = WCAGChecker(url)
            checker.check_all()
            
            all_results.append({
                'url': url,
                'issues': len(checker.issues),
                'warnings': len(checker.warnings),
                'passed': len(checker.passed)
            })
            
        except Exception as e:
            print(f"{Fore.RED}Error checking {url}: {str(e)}{Style.RESET_ALL}")
            all_results.append({
                'url': url,
                'error': str(e)
            })
    
    # Print overall summary if multiple URLs
    if len(urls) > 1:
        print(f"\n\n{Fore.CYAN}{'='*70}")
        print(f"OVERALL SUMMARY ({len(urls)} pages checked)")
        print(f"{'='*70}{Style.RESET_ALL}")
        
        for result in all_results:
            if 'error' in result:
                print(f"\n{Fore.RED}✗ {result['url']}{Style.RESET_ALL}")
                print(f"  Error: {result['error']}")
            else:
                status_color = Fore.GREEN if result['issues'] == 0 else Fore.RED
                print(f"\n{status_color}• {result['url']}{Style.RESET_ALL}")
                print(f"  Issues: {result['issues']}, Warnings: {result['warnings']}, Passed: {result['passed']}")


if __name__ == "__main__":
    main()
