
import os
import re
from pathlib import Path
from markitdown import MarkItDown

class ChapterConverter:
    def __init__(self):
        self.md = MarkItDown()
        self.equation_counter = {}
        
    def clean_text(self, text):
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Clean up common OCR artifacts
        text = re.sub(r'[^\w\s\-.,;:!?()\'\"]+', '', text)
        # Fix common punctuation issues
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        return text.strip()
    
    def detect_structure_type(self, line):
        """Detect the type of content structure"""
        line_clean = line.strip().lower()
        
        # Chapter titles
        if re.match(r'^chapter\s+\d+', line_clean) or re.match(r'^ch\s*\d+', line_clean):
            return 'chapter_title'
        
        # Major sections (numbered)
        if re.match(r'^\d+\.\s+[A-Z]', line.strip()):
            return 'major_section'
        
        # Subsections (numbered)
        if re.match(r'^\d+\.\d+\s+[A-Z]', line.strip()):
            return 'subsection'
        
        # Special content blocks
        if any(keyword in line_clean for keyword in [
            'activity', 'exercise', 'questions', 'discuss', 'new words', 
            'source', 'box', 'think about it', 'do you know', 'remember'
        ]):
            return 'special_block'
        
        # Lists and bullet points
        if re.match(r'^[-•*]\s+', line.strip()) or re.match(r'^\d+\.\s+[a-z]', line.strip()):
            return 'list_item'
        
        # Regular paragraph
        return 'paragraph'
    
    def format_markdown(self, content, chapter_num=None):
        """Apply enhanced formatting rules to the converted markdown"""
        lines = content.split('\n')
        formatted_lines = []
        current_chapter = chapter_num
        in_special_block = False
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            # Skip empty lines but preserve some spacing
            if not line:
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                continue
            
            # Clean the text content
            line = self.clean_text(line)
            if not line:
                continue
                
            structure_type = self.detect_structure_type(line)
            
            # Handle different content types
            if structure_type == 'chapter_title':
                # Extract chapter info
                chapter_match = re.search(r'chapter\s+(\d+)', line.lower())
                if chapter_match:
                    current_chapter = chapter_match.group(1)
                
                # Clean chapter title
                title = re.sub(r'^chapter\s*\d*\s*:?\s*', '', line, flags=re.IGNORECASE)
                formatted_lines.append('')
                formatted_lines.append(f'# Chapter {current_chapter} : {title}')
                formatted_lines.append('')
                
            elif structure_type == 'major_section':
                # Format as major section
                formatted_lines.append('')
                formatted_lines.append(f'## {line}')
                formatted_lines.append('')
                
            elif structure_type == 'subsection':
                # Format as subsection
                formatted_lines.append('')
                formatted_lines.append(f'### {line}')
                formatted_lines.append('')
                
            elif structure_type == 'special_block':
                # Format special content blocks
                if not in_special_block:
                    formatted_lines.append('')
                    formatted_lines.append('---')
                
                # Detect specific block types
                if 'new words' in line.lower():
                    formatted_lines.append(f'#### New Words')
                elif 'activity' in line.lower():
                    formatted_lines.append(f'#### Activity')
                elif 'discuss' in line.lower():
                    formatted_lines.append(f'#### Discuss')
                elif 'source' in line.lower():
                    formatted_lines.append(f'#### Source')
                elif 'box' in line.lower():
                    formatted_lines.append(f'#### Box')
                else:
                    formatted_lines.append(f'#### {line}')
                
                in_special_block = True
                
            elif structure_type == 'list_item':
                # Handle list items
                if in_special_block:
                    formatted_lines.append('')
                    formatted_lines.append('---')
                    formatted_lines.append('')
                    in_special_block = False
                
                # Format list item
                if re.match(r'^[-•*]\s+', line):
                    formatted_lines.append(f'- {line[2:].strip()}')
                else:
                    formatted_lines.append(line)
                    
            else:
                # Regular paragraph
                if in_special_block and not any(keyword in line.lower() for keyword in ['activity', 'exercise', 'discuss', 'source']):
                    formatted_lines.append('')
                    formatted_lines.append('---')
                    formatted_lines.append('')
                    in_special_block = False
                
                # Improve text formatting
                # Handle quotes and emphasis
                line = re.sub(r'"([^"]+)"', r'"\1"', line)
                line = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', line)
                
                # Handle equations and formulas
                if '$$' in line or re.search(r'\b[A-Z][a-z]*\s*=\s*', line):
                    chapter_key = f"ch_{current_chapter}"
                    if chapter_key not in self.equation_counter:
                        self.equation_counter[chapter_key] = 0
                    self.equation_counter[chapter_key] += 1
                    equation_label = f"(Equation {current_chapter}.{self.equation_counter[chapter_key]})"
                    line = line + f' {equation_label}'
                
                # Ensure proper paragraph spacing
                if line.endswith('.') or line.endswith('!') or line.endswith('?'):
                    formatted_lines.append(line)
                    # Check if next line starts a new paragraph
                    if i + 1 < len(lines) and lines[i + 1].strip():
                        next_line_type = self.detect_structure_type(lines[i + 1])
                        if next_line_type in ['paragraph', 'major_section', 'subsection']:
                            formatted_lines.append('')
                else:
                    formatted_lines.append(line)
        
        # Clean up the final output
        result = '\n'.join(formatted_lines)
        
        # Remove excessive blank lines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Ensure sections are properly separated
        result = re.sub(r'(#{1,4}\s+[^\n]+)\n([^\n#])', r'\1\n\n\2', result)
        
        return result
    
    def convert_pdf_to_markdown(self, pdf_path, output_path):
        """Convert a single PDF to markdown with enhanced formatting"""
        try:
            # Extract chapter number and subject from filename
            filename = Path(pdf_path).stem
            subject_path = Path(pdf_path).parent.name
            
            chapter_match = re.search(r'CH\s*(\d+)', filename)
            chapter_num = chapter_match.group(1) if chapter_match else "1"
            
            print(f"Converting {pdf_path}...")
            print(f"  Subject: {subject_path}")
            print(f"  Chapter: {chapter_num}")
            
            # Convert PDF to markdown with error handling
            try:
                result = self.md.convert(pdf_path)
                raw_markdown = result.text_content
                
                if not raw_markdown or len(raw_markdown.strip()) < 100:
                    print(f"  ⚠ Warning: Extracted content seems too short ({len(raw_markdown)} chars)")
                    
            except Exception as conv_error:
                print(f"  ✗ PDF conversion failed: {str(conv_error)}")
                return False
            
            # Apply custom formatting
            try:
                formatted_markdown = self.format_markdown(raw_markdown, chapter_num)
                
                # Add metadata header
                metadata_header = f"""---
title: "{subject_path} - Chapter {chapter_num}"
subject: "{subject_path}"
chapter: {chapter_num}
source_file: "{pdf_path.name}"
generated_on: "{Path().cwd().name}"
---

"""
                formatted_markdown = metadata_header + formatted_markdown
                
            except Exception as format_error:
                print(f"  ✗ Formatting failed: {str(format_error)}")
                # Fallback to basic formatting
                formatted_markdown = f"# {subject_path} - Chapter {chapter_num}\n\n{raw_markdown}"
            
            # Write to output file with better error handling
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_markdown)
                
                # Verify file was written
                file_size = output_path.stat().st_size
                print(f"  ✓ Successfully converted to {output_path}")
                print(f"  📄 Output size: {file_size:,} bytes")
                return True
                
            except Exception as write_error:
                print(f"  ✗ Failed to write output file: {str(write_error)}")
                return False
            
        except Exception as e:
            print(f"✗ Unexpected error converting {pdf_path}: {str(e)}")
            import traceback
            print(f"  Details: {traceback.format_exc()}")
            return False
    
    def convert_all_chapters(self):
        """Convert all PDF chapters to markdown with enhanced processing"""
        base_dir = Path('.')
        output_dir = Path('markdown_output')
        output_dir.mkdir(exist_ok=True)
        
        # Find all PDF files in subject directories
        pdf_files = []
        subjects = {}
        
        for subject_dir in base_dir.iterdir():
            if subject_dir.is_dir() and subject_dir.name.startswith('CLASS'):
                subject_pdfs = list(subject_dir.glob('*.pdf'))
                if subject_pdfs:
                    pdf_files.extend(subject_pdfs)
                    subjects[subject_dir.name] = len(subject_pdfs)
        
        if not pdf_files:
            print("❌ No PDF files found in CLASS directories")
            print("\nSearched for directories starting with 'CLASS'")
            return
        
        # Display found files summary
        print("📚 PDF to Markdown Converter")
        print("=" * 50)
        print(f"📁 Found {len(pdf_files)} PDF files across {len(subjects)} subjects:")
        
        for subject, count in subjects.items():
            print(f"  • {subject}: {count} chapters")
        
        print(f"\n🎯 Starting conversion process...")
        print(f"📤 Output directory: {output_dir.absolute()}")
        print("-" * 50)
        
        successful = 0
        failed = 0
        failed_files = []
        
        # Convert each file with progress tracking
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing...")
            
            # Create organized output structure
            subject = pdf_file.parent.name
            chapter = pdf_file.stem
            
            # Clean filename for better organization
            clean_subject = re.sub(r'^CLASS\s*\d*\s*-\s*', '', subject)
            output_filename = f"{clean_subject}_{chapter}.md"
            output_path = output_dir / output_filename
            
            if self.convert_pdf_to_markdown(pdf_file, output_path):
                successful += 1
                print(f"  ✅ Success!")
            else:
                failed += 1
                failed_files.append(str(pdf_file))
                print(f"  ❌ Failed!")
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 CONVERSION SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully converted: {successful}/{len(pdf_files)} files")
        print(f"❌ Failed conversions: {failed}/{len(pdf_files)} files")
        
        if failed_files:
            print(f"\n⚠️  Failed files:")
            for failed_file in failed_files:
                print(f"   • {failed_file}")
        
        print(f"\n📂 All output files saved to: {output_dir.absolute()}")
        
        if successful > 0:
            print(f"\n🎉 Ready to use! Check the markdown files for:")
            print(f"   • Proper chapter structure")
            print(f"   • Formatted headings and sections")
            print(f"   • Special blocks (Activities, Discussions, etc.)")
            print(f"   • Clean paragraph formatting")
        
        return {"successful": successful, "failed": failed, "total": len(pdf_files)}

def main():
    print("PDF to Markdown Converter")
    print("=" * 50)
    
    converter = ChapterConverter()
    converter.convert_all_chapters()

if __name__ == "__main__":
    main()
