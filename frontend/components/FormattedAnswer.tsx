import React from 'react';
import styles from '../styles/Answer.module.css';

interface FormattedAnswerProps {
  answer: string;
}

export default function FormattedAnswer({ answer }: FormattedAnswerProps) {
  // Function to parse the AI response and extract sections
  const parseAnswer = (text: string) => {
    const sections: { type: string; title: string; content: string }[] = [];
    
    // Try to extract structured sections using a different approach
    const textParts = text.split(/\*\*[^*]+\*\*/);
    const markers = text.match(/\*\*[^*]+\*\*/g) || [];
    
    let localContextContent = '';
    let webSearchContent = '';
    let finalAnswerContent = '';
    
    // Find the sections by looking for specific markers
    for (let i = 0; i < markers.length; i++) {
      const marker = markers[i];
      const nextPart = textParts[i + 1] || '';
      
      if (marker.includes('What I found in the local context')) {
        // Find the end of this section
        const nextMarkerIndex = markers.findIndex((m, idx) => idx > i && 
          (m.includes('Did I need to search the web') || m.includes('Comprehensive final answer')));
        
        if (nextMarkerIndex > i) {
          localContextContent = text.substring(
            text.indexOf(marker) + marker.length,
            text.indexOf(markers[nextMarkerIndex])
          ).trim();
        }
      } else if (marker.includes('What additional information I found through web search')) {
        // Find the end of this section
        const nextMarkerIndex = markers.findIndex((m, idx) => idx > i && m.includes('Comprehensive final answer'));
        
        if (nextMarkerIndex > i) {
          webSearchContent = text.substring(
            text.indexOf(marker) + marker.length,
            text.indexOf(markers[nextMarkerIndex])
          ).trim();
        }
      } else if (marker.includes('Comprehensive final answer')) {
        finalAnswerContent = text.substring(text.indexOf(marker) + marker.length).trim();
      }
    }
    
    if (localContextContent) {
      sections.push({
        type: 'local',
        title: 'Local Knowledge Base',
        content: localContextContent
      });
    }
    
    if (webSearchContent) {
      sections.push({
        type: 'web',
        title: 'Web Search Results',
        content: webSearchContent
      });
    }
    
    if (finalAnswerContent) {
      sections.push({
        type: 'final',
        title: 'Comprehensive Answer',
        content: finalAnswerContent
      });
    }
    
    // If no structured sections found, treat as regular text
    if (sections.length === 0) {
      return { isStructured: false, content: text };
    }
    
    return { isStructured: true, sections };
  };

  const parsed = parseAnswer(answer);

  if (!parsed.isStructured) {
    // For non-structured responses, just format as regular paragraphs
    return (
      <div className={styles.answerContent}>
        {answer.split('\n\n').map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
    );
  }

  return (
    <div className={styles.answerContent}>
      {parsed.sections?.map((section, index) => {
        let sectionClass = styles.answerSection;
        if (section.type === 'local') sectionClass += ` ${styles.localContextSection}`;
        if (section.type === 'web') sectionClass += ` ${styles.webSearchSection}`;
        if (section.type === 'final') sectionClass += ` ${styles.finalAnswerSection}`;
        
        return (
          <div key={index} className={sectionClass}>
            <div className={styles.answerSectionTitle}>
              {section.title}
            </div>
            <div className={styles.answerSectionContent}>
              {formatContent(section.content)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Function to format content with proper styling
function formatContent(content: string): React.ReactNode {
  // Split into paragraphs
  const paragraphs = content.split('\n\n');
  
  return paragraphs.map((paragraph, index) => {
    if (paragraph.trim() === '') return null;
    
    // Check if paragraph contains a numbered list
    if (paragraph.match(/^\d+\./)) {
      const lines = paragraph.split('\n');
      const listItems = lines.map((line, lineIndex) => {
        const match = line.match(/^(\d+)\.\s*(.*)/);
        if (match) {
          return (
            <div key={lineIndex} className={styles.listItem}>
              <span className={styles.boldText}>{match[1]}.</span> {match[2]}
            </div>
          );
        }
        return <div key={lineIndex}>{line}</div>;
      });
      
      return <div key={index}>{listItems}</div>;
    }
    
    // Check for bold text (wrapped in **)
    const formattedParagraph = paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    return (
      <p 
        key={index} 
        dangerouslySetInnerHTML={{ __html: formattedParagraph }}
      />
    );
  });
} 