import React, { useState, useRef, useEffect } from 'react';
import { Button, Container, Row, Table, Col, Form, Modal } from 'react-bootstrap';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';
import '../styles/ReviewFinder.css';
import config from '../config/config';

interface Review {
  user: string;
  rating: number;
  review: string;
  reviewCreatedVersion: string;
  thumbsUpCount: number;
  date: string;
  isExpanded?: boolean; // To manage expanded state of reviews
}

interface SubscriptionForm {
  email: string;
  topics: string[];
}

interface Category {
  name: string;
  products: string[];
}

const categories: Category[] = [
  {
    name: 'FortiGate & Network Security',
    products: ['FortiGate', 'FortiGate Cloud', 'FortiGate-VM', 'FortiOS', 'FortiGuard', 'FortiCare']
  },
  {
    name: 'Cloud Security',
    products: ['FortiCNP', 'FortiWeb Cloud', 'FortiMail Cloud', 'FortiADC Cloud', 'FortiToken Cloud', 'FortiCASB', 'FortiCWP', 'FortiGSLB Cloud', 'FortiSASE', 'FortiWeb Cloud WAF-as-a-Service', 'FortiCDN', 'FortiCloud']
  },
  {
    name: 'Access & Identity',
    products: ['FortiAuthenticator', 'FortiToken', 'FortiToken Mobile', 'FortiClient', 'FortiClient Cloud', 'FortiPass', 'FortiTrust Identity']
  },
  {
    name: 'Management & Analytics',
    products: ['FortiManager', 'FortiManager Cloud', 'FortiAnalyzer', 'FortiAnalyzer Cloud', 'FortiCloud Analytics', 'FortiSOAR', 'FortiMonitor', 'FortiPortal', 'FortiReporter']
  },
  {
    name: 'Security Operations',
    products: ['FortiSIEM', 'FortiEDR', 'FortiXDR', 'FortiNDR', 'FortiDeceptor', 'FortiSandbox', 'FortiSandbox Cloud', 'FortiAI', 'FortiInsight', 'FortiResponder']
  },
  {
    name: 'Email & Web Security',
    products: ['FortiMail', 'FortiWeb', 'FortiIsolator', 'FortiProxy', 'FortiCache']
  },
  {
    name: 'Network Access',
    products: ['FortiNAC', 'FortiAP', 'FortiSwitch', 'FortiSwitch Cloud', 'FortiLAN Cloud', 'FortiExtender', 'FortiPresence']
  },
  {
    name: 'Voice & Communications',
    products: ['FortiVoice', 'FortiVoice Cloud', 'FortiFone', 'FortiCall']
  },
  {
    name: 'SD-WAN & Networking',
    products: ['FortiWAN', 'FortiSD-WAN', 'FortiGSLB', 'FortiDDoS', 'FortiBalancer', 'FortiADC', 'FortiDNS', 'FortiIPAM']
  },
  {
    name: 'IoT & OT Security',
    products: ['FortiNAC', 'FortiSilent', 'FortiGuard OT', 'FortiOT']
  },
  {
    name: 'Mobile Security',
    products: ['FortiSIM', 'FortiCarrier']
  },
  {
    name: 'Tools & Applications',
    products: ['FortiExplorer', 'FortiExplorer Go', 'FortiConverter', 'FortiTester', 'FortiRecorder', 'FortiCamera']
  },
  {
    name: 'Specialized Solutions',
    products: ['FortiPenTest', 'FortiPhish', 'FortiRecon', 'FortiDevSec', 'FortiRASA']
  },
  {
    name: 'Services',
    products: ['FortiTrust', 'FortiCare', 'FortiGuard Services', 'FortiSupport', 'FortiCloud Services', 'FortiPro Services', 'FortiCare Elite', 'FortiCare Premium', 'FortiTrust Identity', 'FortiTrust Security', 'FortiTrust Access']
  }
];

const fetchReviews = async (platform: string, app_name: string, app_id?: string): Promise<Review[]> => {
  let apiUrl = `${config.reviewfinderUrl}/reviewfinder/v1/${platform}/${app_name}`;
  if (app_id) {
    apiUrl = `${config.reviewfinderUrl}/reviewfinder/v1/${platform}/${app_name}/${app_id}`;
  }
  try {
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`Error fetching reviews: ${response.statusText}`);
    }
    const data = await response.json();
    return data.reviews || [];
  } catch (error) {
    console.error(error);
    return [];
  }
};

const subscribeToTopics = async (email: string, topics: string[]): Promise<boolean> => {
  try {
    const response = await fetch(`${config.reviewfinderUrl}/reviewfinder/v1/subscriptions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        topic: topics,
      }),
    });

    if (!response.ok) {
      throw new Error(`Error subscribing: ${response.statusText}`);
    }

    return true;
  } catch (error) {
    console.error(error);
    return false;
  }
};

const ReviewFinder: React.FC = () => {
  const [appName, setAppName] = useState('');
  const [appId, setAppId] = useState('');
  const [platform, setPlatform] = useState('');
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [filterRating, setFilterRating] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState(''); // To store content for popup
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const [subscriptionForm, setSubscriptionForm] = useState<SubscriptionForm>({
    email: '',
    topics: [],
  });
  const [subscriptionError, setSubscriptionError] = useState<string | null>(null);
  const [subscriptionSuccess, setSubscriptionSuccess] = useState<string | null>(null);
  const reviewsPerPage = 10;
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [visibleItems, setVisibleItems] = useState<number>(10);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const [showUnsubscribeModal, setShowUnsubscribeModal] = useState(false);
  const [unsubscribeEmail, setUnsubscribeEmail] = useState('');
  const [unsubscribeError, setUnsubscribeError] = useState<string | null>(null);
  const [unsubscribeSuccess, setUnsubscribeSuccess] = useState<string | null>(null);

  const toggleCategory = (categoryName: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryName)) {
        newSet.delete(categoryName);
      } else {
        newSet.add(categoryName);
      }
      return newSet;
    });
  };

  const handleScroll = () => {
    if (dropdownRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = dropdownRef.current;
      if (scrollHeight - scrollTop <= clientHeight * 1.5) {
        setVisibleItems(prev => prev + 10);
      }
    }
  };

  useEffect(() => {
    if (dropdownRef.current) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              setVisibleItems(prev => prev + 10);
            }
          });
        },
        { threshold: 0.5 }
      );

      const lastItem = dropdownRef.current.lastElementChild;
      if (lastItem) {
        observerRef.current.observe(lastItem);
      }
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [visibleItems]);

  const filteredCategories = categories.map(category => ({
    ...category,
    products: category.products.filter(product =>
      product.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(category => category.products.length > 0);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  useEffect(() => {
    if (!showSubscriptionModal) {
      setShowDropdown(false);
      setSearchTerm('');
    }
  }, [showSubscriptionModal]);

  const handleTopicSelect = (topic: string) => {
    if (!selectedTopics.includes(topic)) {
      setSelectedTopics([...selectedTopics, topic]);
      setSubscriptionForm(prev => ({
        ...prev,
        topics: [...selectedTopics, topic]
      }));
    }
    setSearchTerm('');
    setShowDropdown(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setShowDropdown(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setShowDropdown(false);
    } else if (e.key === 'ArrowDown' && showDropdown && filteredCategories.length > 0) {
      e.preventDefault();
      const currentIndex = filteredCategories.findIndex(category => category.name === document.activeElement?.textContent);
      const nextIndex = (currentIndex + 1) % filteredCategories.length;
      const nextElement = document.querySelector(`[data-topic="${filteredCategories[nextIndex].name}"]`);
      if (nextElement) {
        (nextElement as HTMLElement).focus();
      }
    } else if (e.key === 'ArrowUp' && showDropdown && filteredCategories.length > 0) {
      e.preventDefault();
      const currentIndex = filteredCategories.findIndex(category => category.name === document.activeElement?.textContent);
      const prevIndex = (currentIndex - 1 + filteredCategories.length) % filteredCategories.length;
      const prevElement = document.querySelector(`[data-topic="${filteredCategories[prevIndex].name}"]`);
      if (prevElement) {
        (prevElement as HTMLElement).focus();
      }
    } else if (e.key === 'Enter' && showDropdown && document.activeElement?.hasAttribute('data-topic')) {
      e.preventDefault();
      const topic = document.activeElement.textContent;
      if (topic) {
        handleTopicSelect(topic);
      }
    }
  };

  const removeTopic = (topicToRemove: string) => {
    const newTopics = selectedTopics.filter(topic => topic !== topicToRemove);
    setSelectedTopics(newTopics);
    setSubscriptionForm(prev => ({
      ...prev,
      topics: newTopics
    }));
  };

  const handleSubscriptionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubscriptionError(null);
    setSubscriptionSuccess(null);

    if (!subscriptionForm.email || selectedTopics.length === 0) {
      setSubscriptionError('Please provide an email and select at least one topic');
      return;
    }

    const success = await subscribeToTopics(subscriptionForm.email, selectedTopics);
    if (success) {
      setSubscriptionSuccess('Successfully subscribed!');
      setSubscriptionForm({ email: '', topics: [] });
      setSelectedTopics([]);
      setTimeout(() => {
        setShowSubscriptionModal(false);
        setSubscriptionSuccess(null);
      }, 2000);
    } else {
      setSubscriptionError('Failed to subscribe. Please try again.');
    }
  };

  const fetchAndDisplayReviews = async () => {
    if (!platform || !appName || (platform === 'App Store' && !appId)) {
      setError('Please fill in all required fields.');
      return;
    }

    setError(null);
    const fetchedReviews = await fetchReviews(platform, appName, appId);
    if (fetchedReviews.length === 0) {
      setError('No reviews found or failed to fetch reviews.');
    }
    setReviews(fetchedReviews);
    setCurrentPage(1);
  };

  const getTotalPages = () => {
    const filteredReviews = filterRating
      ? reviews.filter((review) => review.rating === filterRating)
      : reviews;
    return Math.ceil(filteredReviews.length / reviewsPerPage);
  };

  const downloadExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(reviews);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Reviews');
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/octet-stream' });
    saveAs(blob, `${appName}_reviews.xlsx`);
  };

  const getPagedReviews = () => {
    const filteredReviews = filterRating
      ? reviews.filter((review) => review.rating === filterRating)
      : reviews;
    const startIndex = (currentPage - 1) * reviewsPerPage;
    const endIndex = startIndex + reviewsPerPage;
    return filteredReviews.slice(startIndex, endIndex);
  };

  const handleShowMore = (content: string) => {
    setModalContent(content);
    setShowModal(true);
  };

  const renderPagination = () => {
    const totalFilteredPages = getTotalPages(); // Dynamically calculate total pages
    const pageButtons = [];
    const maxVisiblePages = 3;

    const startPage = Math.max(currentPage - 1, 1);
    const endPage = Math.min(startPage + maxVisiblePages - 1, totalFilteredPages);

    if (startPage > 1) {
      pageButtons.push(
        <Button key="start-ellipsis" variant="link" disabled>
          ...
        </Button>
      );
    }

    for (let i = startPage; i <= endPage; i++) {
      pageButtons.push(
        <Button
          key={i}
          variant={currentPage === i ? 'primary' : 'link'}
          onClick={() => setCurrentPage(i)}
        >
          {i}
        </Button>
      );
    }

    if (endPage < totalFilteredPages) {
      pageButtons.push(
        <Button key="end-ellipsis" variant="link" disabled>
          ...
        </Button>
      );
    }

    return pageButtons;
  };

  const clearAllTopics = () => {
    setSelectedTopics([]);
    setSubscriptionForm(prev => ({
      ...prev,
      topics: []
    }));
  };

  const handleUnsubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    setUnsubscribeError(null);
    setUnsubscribeSuccess(null);

    if (!unsubscribeEmail) {
      setUnsubscribeError('Please enter your email address');
      return;
    }

    try {
      const response = await fetch(`${config.reviewfinderUrl}/reviewfinder/v1/subscriptions`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: unsubscribeEmail
        }),
      });

      if (!response.ok) {
        throw new Error(`Error unsubscribing: ${response.statusText}`);
      }

      setUnsubscribeSuccess('Successfully unsubscribed!');
      setUnsubscribeEmail('');
      setTimeout(() => {
        setShowUnsubscribeModal(false);
        setUnsubscribeSuccess(null);
      }, 2000);
    } catch (error) {
      console.error(error);
      setUnsubscribeError('Failed to unsubscribe. Please try again.');
    }
  };

  return (
    <Container>
      <Row className="mb-10">
        <Col xs={2}>
          <Form.Group controlId="platform">
            <Form.Label>Platform</Form.Label>
            <Form.Control
              as="select"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              <option value="">Select Platform</option>
              <option value="google_play">Google Play</option>
              <option value="apple_store">App Store</option>
              <option value="reddit">Reddit</option>
            </Form.Control>
          </Form.Group>
        </Col>

        {platform === 'google_play' && (
          <Col xs={2}>
            <Form.Group controlId="appName">
              <Form.Label>App Name</Form.Label>
              <Form.Control
                type="text"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
              />
            </Form.Group>
          </Col>
        )}

        {platform === 'apple_store' && (
          <>
            <Col xs={2}>
              <Form.Group controlId="appName">
                <Form.Label>App Name</Form.Label>
                <Form.Control
                  type="text"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                />
              </Form.Group>
            </Col>
            <Col xs={2}>
              <Form.Group controlId="appId">
                <Form.Label>App ID</Form.Label>
                <Form.Control
                  type="text"
                  value={appId}
                  onChange={(e) => setAppId(e.target.value)}
                />
              </Form.Group>
            </Col>
          </>
        )}

        {platform && (
          <Col xs={2}>
            <Form.Group controlId="filterRating">
              <Form.Label>Filter by Rating</Form.Label>
              <Form.Control
                as="select"
                value={filterRating ?? ''}
                onChange={(e) =>
                  setFilterRating(e.target.value ? parseInt(e.target.value, 10) : null)
                }
              >
                <option value="">All Ratings</option>
                <option value="1">1 Star</option>
                <option value="2">2 Stars</option>
                <option value="3">3 Stars</option>
                <option value="4">4 Stars</option>
                <option value="5">5 Stars</option>
              </Form.Control>
            </Form.Group>
          </Col>
        )}
      </Row>

      <Row className="mb-4">
        <Col className="text-center">
          <Button variant="primary" onClick={fetchAndDisplayReviews} className="me-3">
            Fetch Reviews
          </Button>
          <Button variant="secondary" onClick={() => window.location.reload()} className="me-3">
            Refresh
          </Button>
          {reviews.length > 0 && (
            <Button variant="success" onClick={downloadExcel} className="me-3">
              Download
            </Button>
          )}
          <Button variant="info" onClick={() => setShowSubscriptionModal(true)} className="me-3">
            Subscribe to Topics
          </Button>
          <Button variant="outline-danger" onClick={() => setShowUnsubscribeModal(true)}>
            Unsubscribe
          </Button>
        </Col>
      </Row>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {reviews.length > 0 && (
        <div>
          <h2>Reviews</h2>
          <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>Username</th>
              <th>Rating</th>
              <th>Content</th>
              <th>Review Version</th>
              <th>Thumbs Up Count</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {getPagedReviews().map((review, index) => (
              <tr key={index}>
                <td>{review.user}</td>
                <td>{review.rating}</td>
                <td>{review.review.length > 50
                    ? `${review.review.slice(0, 50)}...`
                    : review.review}
                  {review.review.length > 50 && (
                    <span
                      style={{
                        cursor: 'pointer',
                        color: 'blue',
                        textDecoration: 'underline',
                        marginLeft: '5px',
                      }}
                      onClick={() => handleShowMore(review.review)}
                    >
                      Show More
                    </span>
                  )}</td>
                <td>{review.reviewCreatedVersion}</td>
                <td>{review.thumbsUpCount}</td>
                <td>{review.date}</td>
              </tr>
            ))}
          </tbody>
        </Table>
          <div className="d-flex justify-content-center mt-3">
            <Button
              onClick={() => setCurrentPage(Math.max(currentPage - 1, 1))}
              disabled={currentPage === 1}
              variant="secondary"
              style={{ marginRight: '5px' }}
            >
              Previous
            </Button>
            {renderPagination()}
            <Button
              onClick={() => setCurrentPage(Math.min(currentPage + 1, getTotalPages()))}
              disabled={currentPage === getTotalPages()}
              variant="secondary"
              style={{ marginLeft: '5px' }}
            >
              Next
            </Button>
            <div style={{ marginLeft: '15px', alignSelf: 'center' }}>
              Page {currentPage} of {getTotalPages()}
            </div>
          </div>
        </div>
      )}

      {/* Subscription Modal */}
      <Modal show={showSubscriptionModal} onHide={() => setShowSubscriptionModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Subscribe to Topics</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubscriptionSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={subscriptionForm.email}
                onChange={(e) => setSubscriptionForm(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Enter your email"
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Select Topics</Form.Label>
              <div style={{ position: 'relative' }}>
                <Form.Control
                  type="text"
                  value={searchTerm}
                  onChange={handleInputChange}
                  onClick={() => setShowDropdown(true)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type to search or click to select topics"
                  autoComplete="off"
                />
                {showDropdown && (
                  <div
                    ref={dropdownRef}
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      maxHeight: '300px',
                      overflowY: 'auto',
                      backgroundColor: 'white',
                      border: '1px solid #ced4da',
                      borderRadius: '0.25rem',
                      zIndex: 1000,
                    }}
                    onScroll={handleScroll}
                  >
                    {filteredCategories.slice(0, visibleItems).map((category) => (
                      <div key={category.name}>
                        <div
                          style={{
                            padding: '8px 12px',
                            backgroundColor: '#f8f9fa',
                            cursor: 'pointer',
                            borderBottom: '1px solid #eee',
                            fontWeight: 'bold',
                          }}
                          onClick={() => toggleCategory(category.name)}
                        >
                          {expandedCategories.has(category.name) ? '▼' : '▶'} {category.name}
                        </div>
                        {expandedCategories.has(category.name) && category.products.map((product) => (
                          <div
                            key={product}
                            data-topic={product}
                            tabIndex={0}
                            style={{
                              padding: '8px 12px 8px 24px',
                              cursor: 'pointer',
                              borderBottom: '1px solid #eee',
                              outline: 'none',
                            }}
                            onClick={() => handleTopicSelect(product)}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = '#f8f9fa';
                              e.currentTarget.focus();
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = 'white';
                            }}
                            onFocus={(e) => {
                              e.currentTarget.style.backgroundColor = '#f8f9fa';
                            }}
                            onBlur={(e) => {
                              e.currentTarget.style.backgroundColor = 'white';
                            }}
                          >
                            {product}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="mt-2">
                {selectedTopics.length > 0 && (
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="text-muted">Selected Topics:</span>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={clearAllTopics}
                    >
                      Clear All
                    </Button>
                  </div>
                )}
                <div className="d-flex flex-wrap">
                  {selectedTopics.map((topic) => (
                    <span
                      key={topic}
                      className="badge bg-primary me-2 mb-2"
                      style={{ fontSize: '0.9rem', padding: '5px 10px' }}
                    >
                      {topic}
                      <button
                        type="button"
                        className="btn-close btn-close-white ms-2"
                        style={{ fontSize: '0.6rem' }}
                        onClick={() => removeTopic(topic)}
                        aria-label="Remove"
                      />
                    </span>
                  ))}
                </div>
              </div>
            </Form.Group>
            {subscriptionError && <p className="text-danger">{subscriptionError}</p>}
            {subscriptionSuccess && <p className="text-success">{subscriptionSuccess}</p>}
            <Button variant="primary" type="submit">
              Subscribe
            </Button>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Unsubscribe Modal */}
      <Modal show={showUnsubscribeModal} onHide={() => setShowUnsubscribeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Unsubscribe from Topics</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleUnsubscribe}>
            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={unsubscribeEmail}
                onChange={(e) => setUnsubscribeEmail(e.target.value)}
                placeholder="Enter your email to unsubscribe"
                required
              />
            </Form.Group>
            {unsubscribeError && <p className="text-danger">{unsubscribeError}</p>}
            {unsubscribeSuccess && <p className="text-success">{unsubscribeSuccess}</p>}
            <div className="d-flex justify-content-between">
              <Button variant="secondary" onClick={() => setShowUnsubscribeModal(false)}>
                Cancel
              </Button>
              <Button variant="danger" type="submit">
                Unsubscribe
              </Button>
            </div>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Existing Modal for Showing Full Content */}
      <Modal show={showModal} onHide={() => setShowModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Full Review Content</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ backgroundColor: 'rgba(255,255,255,0.8)' }}>
          <p>{modalContent}</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default ReviewFinder;
