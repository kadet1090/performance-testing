<?php

namespace App\CommonMark;

use Kadet\Highlighter\Formatter\HtmlFormatter;
use Kadet\Highlighter\KeyLighter;
use League\CommonMark\Block\Element\AbstractBlock;
use League\CommonMark\Block\Element\FencedCode;
use League\CommonMark\Block\Renderer\BlockRendererInterface;
use League\CommonMark\ElementRendererInterface;
use League\CommonMark\HtmlElement;

class KeylighterCodeRenderer implements BlockRendererInterface
{
    private $keylighter;
    private $formatter;

    public function __construct(KeyLighter $keylighter)
    {
        $this->keylighter = $keylighter;
        $this->formatter  = new HtmlFormatter();
    }

    /**
     * @inheritDoc
     */
    public function render(AbstractBlock $block, ElementRendererInterface $htmlRenderer, bool $inTightList = false)
    {
        $language = $this->keylighter->getLanguage($block instanceof FencedCode ? $block->getInfo() : 'plaintext');
        $text     = $block->getStringContent();

        return new HtmlElement('pre', ['class' => 'keylighter'], @$this->keylighter->highlight($text, $language, $this->formatter));
    }
}
