import React, { useState, useEffect } from 'react';
import './App.css';
import './Search_panel.css';

const Fridge = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [newItemName, setNewItemName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [categories, setCategories] = useState([]);
  const [statistics, setStatistics] = useState(null);

  // Python API URL
  const PYTHON_API_URL = 'https://faso312.ru';
  const RESOURCE = 'py';

  // Загрузка категорий из Python
  const loadCategories = async () => {
    try {
      const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/categories`);
      const data = await response.json();
      setCategories(data.categories);
    } catch (err) {
      console.error('Ошибка загрузки категорий:', err);
    }
  };

  // Загрузка статистики
  const loadStatistics = async () => {
    try {
      const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  };

  // Поиск через Python
  const smartSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      console.log('Поиск через Python:', searchQuery);
      
      const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/search-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery
        }),
      });
      
      if (!response.ok) {
        throw new Error('Ошибка поиска');
      }
      
      const data = await response.json();
      setSearchResults(data);
      setError('');
      
      console.log('Результаты поиска:', data);
      
    } catch (err) {
      console.error('Ошибка поиска:', err);
      setError('Ошибка при поиске продуктов');
      setSearchResults(null);
    }
  };

  // Загрузка данных через Python из PostgreSQL
  const fetchItems = async () => {
    try {
      setLoading(true);
      console.log('Загрузка данных из PostgreSQL через Python...');
      
      const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/database-items`);
      
      if (!response.ok) {
        throw new Error(`Python сервер недоступен: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Данные из PostgreSQL:', data);
      
      setItems(data);
      setError('');
      loadStatistics();
    } catch (err) {
      console.error('Error fetching items:', err);
      setError('Ошибка загрузки данных из базы данных');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
    loadCategories();
  }, []);

  const toggleDoor = () => {
    setIsOpen(!isOpen);
  };


  const addItem = async () => {
    const itemName = newItemName.trim();
    if (itemName === '') {
      setError('Введите название продукта');
      return;
    }
    
    try {
      const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/items/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: itemName,
          isInFridge: true,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при добавлении');
      }
      
      const newItem = await response.json();
      setItems([newItem, ...items]);
      setNewItemName('');
      setError('');
      console.log('Продукт добавлен через Python API:', newItem);
      
    } catch (err) {
      console.error('Error adding item:', err);
      setError(err.message || 'Ошибка добавления продукта');
    }
  };

const removeItem = async (id) => {
  if (!window.confirm('Удалить этот продукт?')) return;
  
  try {
    const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/items/remove/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Ошибка при удалении');
    }
    
    const result = await response.json();
    setItems(items.filter(item => item.id !== id));
    setError('');
    console.log('Продукт удален через Python API:', result.message);
    
  } catch (err) {
    console.error('Error deleting item:', err);
    setError(err.message || 'Ошибка удаления продукта');
  }
};

const toggleItemPosition = async (id) => {
  try {
    const response = await fetch(`${PYTHON_API_URL}/${RESOURCE}/items/move/${id}/toggle`, {
      method: 'PATCH',
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Ошибка при перемещении');
    }
    
    const updatedItem = await response.json();
    setItems(items.map(item => 
      item.id === id ? updatedItem : item
    ));
    setError('');
    console.log('Позиция переключена через Python API:', updatedItem);
    
  } catch (err) {
    console.error('Error toggling item:', err);
    setError(err.message || 'Ошибка перемещения продукта');
  }
};


  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      addItem();
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      smartSearch();
    }
  };

  const clearError = () => {
    setError('');
    setSearchResults(null);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  // Фильтруем товары для отображения
  const displayItems = searchResults ? searchResults.items : items;
  const itemsInFridge = displayItems.filter(item => item.is_in_fridge);
  const itemsOutside = displayItems.filter(item => !item.is_in_fridge);

  if (loading) {
    return (
      <div className="fridge-app">
      <h1>Холодильник</h1>
        <div className="loading">Загрузка данных из базы...</div>
      </div>
    );
  }

  return (
    <div className="fridge-app">
      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button onClick={clearError} className="error-close">×</button>
        </div>
      )}

      {/* Панель поиска */}
      <div className="search-panel">
        <h3>Поиск продуктов</h3>
        <div className="search-form">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyUp={handleSearchKeyPress}
            placeholder="Введите категорию или название продукта"
            style={{flex: 1, padding: '10px', border: '1px solid #ddd', borderRadius: '4px'}}
          />
          <button 
            onClick={smartSearch}
            className="search-button"
          >
            Поиск
          </button>
          {searchResults && (
            <button 
              onClick={clearSearch}
              className="clear-button"
            >
              Очистить
            </button>
          )}
        </div>

        {/* Категории */}
        <div className="quick-categories">
          <span>Категории: </span>
          {categories.map(category => (
            <button
              key={category}
              onClick={() => {
                setSearchQuery(category);
                setTimeout(smartSearch, 100);
              }}
              className="category-tag"
            >
              {category}
            </button>
          ))}
        </div>

        {/* Результаты поиска */}
        {searchResults && (
          <div className="search-results">
            <h4>
              Найдено {searchResults.found_count} товаров по запросу: 
              "{searchResults.search_query}"
            </h4>
            {searchResults.items.length === 0 && (
              <p className="empty-message">Товары не найдены</p>
            )}
          </div>
        )}
      </div>

      {/* Статистика */}
      {statistics && (
        <div className="statistics-panel">
          <h4>Статистика: Всего продуктов - {statistics.total_products}</h4>
          <div className="stats-grid">
            {Object.entries(statistics.categories).map(([category, stats]) => (
              <div key={category} className="stat-item">
                <span className="stat-category">{category}:</span>
                <span className="stat-count">{stats.total} шт.</span>
                <span className="stat-fridge">({stats.in_fridge} в холодильнике)</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="fridge-container">
        {/* Холодильник */}
        <div className={`fridge ${isOpen ? 'open' : ''}`}>
          <div className="fridge-door">
            <div className="door-handle" onClick={toggleDoor}></div>
          </div>
          
          {isOpen && (
            <div className="fridge-interior">
              <div className="fridge-content">
                <h3>В холодильнике:</h3>
                {itemsInFridge.length === 0 ? (
                  <p className="empty-message">Холодильник пуст</p>
                ) : (
                  <div className="items-grid">
                    {itemsInFridge.map(item => (
                      <div key={item.id} className="fridge-item">
                        <span className="item-name">{item.name}</span>
                        {item.category && (
                          <span className="item-category">{item.category}</span>
                        )}
                        <div className="item-buttons">
                          <button 
                            onClick={() => toggleItemPosition(item.id)}
                            className="item-btn"
                          >
                            Вынуть
                          </button>
                          <button 
                            onClick={() => removeItem(item.id)}
                            className="item-btn delete"
                          >
                            Удалить
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Продукты снаружи */}
        <div className="outside-items">
          <h3>Рядом с холодильником:</h3>
          {itemsOutside.length === 0 ? (
            <p className="empty-message">Продуктов нет</p>
          ) : (
            <div className="items-grid">
              {itemsOutside.map(item => (
                <div key={item.id} className="fridge-item outside">
                  <span className="item-name">{item.name}</span>
                  {item.category && (
                    <span className="item-category">{item.category}</span>
                  )}
                  <div className="item-buttons">
                    <button 
                      onClick={() => toggleItemPosition(item.id)}
                      className="item-btn"
                    >
                      Положить
                    </button>
                    <button 
                      onClick={() => removeItem(item.id)}
                      className="item-btn delete"
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Панель управления */}
      <div className="control-panel">
        <button 
          onClick={toggleDoor} 
          className={`door-btn ${isOpen ? 'close' : 'open'}`}
        >
          {isOpen ? 'Закрыть холодильник' : 'Открыть холодильник'}
        </button>
        
        <div className="add-item-form">
          <input
            type="text"
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            onKeyUp ={handleKeyPress}
            placeholder="Введите название продукта"
            maxLength={50}
          />
          <button onClick={addItem}>
            Добавить в базу
          </button>
          <button 
          onClick={fetchItems}
        >
          Обновить данные
        </button>
        </div>


      </div>
    </div>
  );
};

export default Fridge;