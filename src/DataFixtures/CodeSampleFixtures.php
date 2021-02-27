<?php

namespace App\DataFixtures;

use App\Entity\Post;
use App\Entity\Tag;
use Doctrine\Bundle\FixturesBundle\Fixture;
use Doctrine\Persistence\ObjectManager;
use Symfony\Component\String\Slugger\SluggerInterface;

class CodeSampleFixtures extends Fixture
{
    /** @var \Symfony\Component\String\Slugger\SluggerInterface */
    private $slugger;

    public function __construct(SluggerInterface $slugger)
    {
        $this->slugger = $slugger;
    }

    public function load(ObjectManager $manager)
    {
        $tag = new Tag();
        $tag->setName('sample');

        $manager->persist($tag);
        $this->addReference('tag-sample', $tag);

        $user = $this->getReference('john_user');

        foreach (glob(__DIR__."/samples/*") as $sample) {
            $post = new Post();
            $post->setTitle($title = "Code Sample: ".basename($sample, '.md'));
            $post->setSlug($this->slugger->slug($title));
            $post->setContent(file_get_contents($sample));
            $post->setAuthor($user);
            $post->setSummary('Lorem ipsum dolor sit amet consectetur adipiscing elit.');
            $post->setPublishedAt(new \DateTime());
            $post->addTag($tag);
            $manager->persist($post);
        }

        $manager->flush();
    }
}
