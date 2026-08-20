import React, { useState, useEffect } from 'react';
import type { CategoryInfo } from '../../types/api';
import { catalogService } from '../../services/catalogService';

interface CategoryPillsProps {
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  onError?: (msg: string) => void;
}

export const CategoryPills: React.FC<CategoryPillsProps> = ({
  selectedCategory,
  onSelectCategory,
  onError,
}) => {
  const [categories, setCategories] = useState<CategoryInfo[]>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchCategories = async () => {
      try {
        const res = await catalogService.getCategories();
        if (isMounted) {
          setCategories(res.categories);
        }
      } catch (err: any) {
        if (isMounted && onError) {
          onError(err.message || 'Failed to load categories');
        }
      }
    };

    fetchCategories();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalDatasets = categories.reduce((sum, c) => sum + c.count, 0);

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
        Filter by Domain
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {/* 'All' category button */}
        <button
          onClick={() => onSelectCategory('All')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.82rem',
            fontWeight: 500,
            background: selectedCategory === 'All' ? 'var(--primary-gradient)' : 'var(--bg-surface)',
            color: selectedCategory === 'All' ? '#fff' : 'var(--text-secondary)',
            border: selectedCategory === 'All' ? '1px solid transparent' : '1px solid var(--border-subtle)',
            boxShadow: selectedCategory === 'All' ? 'var(--shadow-glow)' : 'none',
            transition: 'all 0.15s ease',
          }}
        >
          <span>🌐 All Domains</span>
          <span
            style={{
              fontSize: '0.72rem',
              background: selectedCategory === 'All' ? 'rgba(255, 255, 255, 0.25)' : 'var(--bg-surface-elevated)',
              padding: '1px 6px',
              borderRadius: 'var(--radius-full)',
            }}
          >
            {totalDatasets || 7}
          </span>
        </button>

        {/* Dynamic categories from backend */}
        {categories.map((cat) => {
          const isSelected = selectedCategory === cat.name;
          return (
            <button
              key={cat.name}
              onClick={() => onSelectCategory(cat.name)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.82rem',
                fontWeight: 500,
                background: isSelected ? 'var(--primary-gradient)' : 'var(--bg-surface)',
                color: isSelected ? '#fff' : 'var(--text-secondary)',
                border: isSelected ? '1px solid transparent' : '1px solid var(--border-subtle)',
                boxShadow: isSelected ? 'var(--shadow-glow)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{cat.icon ? `${cat.icon} ` : ''}{cat.name}</span>
              <span
                style={{
                  fontSize: '0.72rem',
                  background: isSelected ? 'rgba(255, 255, 255, 0.25)' : 'var(--bg-surface-elevated)',
                  padding: '1px 6px',
                  borderRadius: 'var(--radius-full)',
                }}
              >
                {cat.count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
